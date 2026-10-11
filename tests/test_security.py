"""Regression checks for untrusted campaign files and spreadsheet exports."""
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
import pandas as pd
import pytest
from utils import data_processing as dp
from utils.exports import export_csv, spreadsheet_safe_frame
from utils.charts import platform_chart, trend_chart


def workbook(raw):
    out = BytesIO()
    raw.to_excel(out, index=False)
    return out.getvalue()


def test_upload_bytes_and_file_type():
    with pytest.raises(dp.DataValidationError, match='10 MB'):
        dp.read_data(b'x' * (dp.MAX_UPLOAD_BYTES + 1), 'data.csv')
    with pytest.raises(dp.DataValidationError, match='UTF-8'):
        dp.read_data(b'abc', 'data.exe')
    with pytest.raises(dp.DataValidationError, match='Cannot read'):
        dp.read_data(b'not a workbook', 'data.xlsx')


@pytest.mark.parametrize('extension', ['csv', 'xlsx'])
def test_parsed_row_bounds(raw, monkeypatch, extension):
    monkeypatch.setattr(dp, 'MAX_ROWS', 2)
    content = raw.head(3).to_csv(index=False).encode() if extension == 'csv' else workbook(raw.head(3))
    with pytest.raises(dp.DataValidationError, match='10,000'):
        dp.read_data(content, 'data.' + extension)


def test_csv_duplicate_headers_and_ragged_rows(raw):
    content = raw.head(1).to_csv(index=False)
    with pytest.raises(dp.DataValidationError, match='unique'):
        dp.read_data(content.replace('Company', 'Campaign_ID', 1).encode(), 'data.csv')
    with pytest.raises(dp.DataValidationError, match='same number'):
        dp.read_data((content + 'one,two\n').encode(), 'data.csv')


def test_long_cell_and_numeric_overflow(raw):
    raw.loc[0, 'Company'] = 'a' * (dp.MAX_CELL_CHARS + 1)
    with pytest.raises(dp.DataValidationError, match='characters'):
        dp.clean_data(raw)
    raw.loc[0, 'Company'] = 'valid'
    raw['Impressions'] = raw.Impressions.astype(object)
    raw.loc[0, 'Impressions'] = 1e30
    with pytest.raises(dp.DataValidationError):
        dp.clean_data(raw)


def test_xlsx_formulas_rejected(raw):
    raw.loc[0, 'Company'] = '=HYPERLINK("https://example.com")'
    with pytest.raises(dp.DataValidationError, match='formulas'):
        dp.read_data(workbook(raw.head(1)), 'data.xlsx')


def test_xlsx_zip_bomb_and_entry_bound(raw, monkeypatch):
    out = BytesIO()
    with ZipFile(out, 'w', ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', 'a' * 1_000_000)
        z.writestr('xl/workbook.xml', '<workbook/>')
    with pytest.raises(dp.DataValidationError, match='decompression'):
        dp.read_data(out.getvalue(), 'bomb.xlsx')
    content = workbook(raw.head(1))
    monkeypatch.setattr(dp, 'MAX_ZIP_ENTRIES', 1)
    with pytest.raises(dp.DataValidationError, match='entries'):
        dp.read_data(content, 'data.xlsx')


def test_xlsx_expansion_bound(raw, monkeypatch):
    monkeypatch.setattr(dp, 'MAX_XLSX_EXPANDED_BYTES', 100)
    with pytest.raises(dp.DataValidationError, match='decompression|expanded'):
        dp.read_data(workbook(raw.head(1)), 'data.xlsx')


def test_xlsx_entity_and_external_link_rejection(raw):
    original = workbook(raw.head(1))
    for path, text in [('extra.xml', '<!DOCTYPE x [<!ENTITY a "hello">]><x>&a;</x>'),
                       ('xl/externalLinks/link.xml', '<x/>')]:
        out = BytesIO()
        with ZipFile(BytesIO(original)) as source, ZipFile(out, 'w', ZIP_DEFLATED) as dest:
            for item in source.infolist():
                dest.writestr(item.filename, source.read(item))
            dest.writestr(path, text)
        with pytest.raises(dp.DataValidationError):
            dp.read_data(out.getvalue(), 'data.xlsx')


@pytest.mark.parametrize('text', ['=1+1', '+cmd', '-cmd', '@SUM(1)', '\t=1+1', '\r=1', '\n=1', '  =1', '\ufeff=1'])
def test_csv_formula_protection_preserves_analytics(text):
    frame = pd.DataFrame({'Company': [text], 'ROI': [-3.2], 'Spend': [100.0]})
    safe = spreadsheet_safe_frame(frame)
    assert safe.Company.iloc[0] == "'" + text
    assert safe.ROI.iloc[0] == -3.2
    assert frame.Company.iloc[0] == text
    decoded = pd.read_csv(BytesIO(export_csv(frame)))
    assert decoded.Company.iloc[0] == "'" + text


def test_chart_html_is_escaped(data):
    from utils.metrics import aggregate_metrics, time_metrics
    data['Channel_Used'] = '<img src=x onerror=alert(1)>'
    platforms = aggregate_metrics(data, 'Channel_Used')
    assert '<img' not in platform_chart(platforms, 'Clicks').data[0].x[0]
    periods = time_metrics(data, 'Weekly')
    periods['Channel_Used'] = data.Channel_Used.iloc[0]
    assert '<img' not in trend_chart(periods, 'Clicks', channel=True).data[0].name


def test_paired_chart_channel_markup_remains_literal(data):
    from utils.charts import paired_chart
    from utils.metrics import time_metrics
    periods = time_metrics(data, 'Weekly')
    periods['Channel_Used'] = '<a href="https://example.com">Channel</a>'
    fig = paired_chart(periods, 'Clicks', 'Conversions', channel=True)
    for trace in fig.data:
        assert '<a' not in trace.name
        assert '&lt;a' in trace.name


def test_false_worksheet_dimensions_cannot_hide_rows(raw, monkeypatch):
    import re
    original = workbook(raw.head(2))
    out = BytesIO()
    with ZipFile(BytesIO(original)) as source, ZipFile(out, 'w', ZIP_DEFLATED) as dest:
        for item in source.infolist():
            content = source.read(item)
            if item.filename == 'xl/worksheets/sheet1.xml':
                content = re.sub(rb'<dimension ref="[^"]+"', b'<dimension ref="A1:P1"', content)
            dest.writestr(item.filename, content)
    monkeypatch.setattr(dp, 'MAX_ROWS', 1)
    with pytest.raises(dp.DataValidationError, match='10,000'):
        dp.read_data(out.getvalue(), 'data.xlsx')


def test_export_html_contains_only_encoded_data(raw, monkeypatch):
    import streamlit as st
    from utils.exports import download_csv
    captured = []
    monkeypatch.setattr(st, 'iframe', lambda document, **kwargs: captured.append(document))
    frame = raw.head(1).copy()
    frame['Company'] = '</a><script>alert(1)</script>'
    download_csv('Download campaign results', frame, 'campaign_results.csv')
    assert '<script>' not in captured[0]
    assert 'data:text/csv;base64,' in captured[0]
    assert '/media/' not in captured[0]


def test_sparse_wide_xlsx_cell_rejected_before_parser(raw):
    original = workbook(raw.head(1))
    out = BytesIO()
    with ZipFile(BytesIO(original)) as source, ZipFile(out, 'w', ZIP_DEFLATED) as dest:
        for item in source.infolist():
            content = source.read(item)
            if item.filename == 'xl/worksheets/sheet1.xml':
                content = content.replace(b'r="A2"', b'r="ZZZ2"')
            dest.writestr(item.filename, content)
    with pytest.raises(dp.DataValidationError, match='64 columns'):
        dp.read_data(out.getvalue(), 'data.xlsx')
