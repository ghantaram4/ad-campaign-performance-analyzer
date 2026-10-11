from io import BytesIO
from datetime import date
import numpy as np
import pandas as pd
import pytest
from utils.data_processing import DataValidationError, apply_filters, clean_data, read_data, search_campaigns
from utils.metrics import aggregate_metrics, compute_metrics, time_metrics

def test_real_dataset_controls(data):
    m = compute_metrics(data)
    assert m['Campaigns'] == 60
    assert m['Spend'] == 29490
    assert m['Clicks'] == 304450
    assert m['Impressions'] == 5450000
    assert m['Conversions'] == 61361
    assert m['CTR'] == pytest.approx(304450 / 5450000)
    assert m['CPC'] == pytest.approx(29490 / 304450)
    assert m['CPA'] == pytest.approx(29490 / 61361)
    assert m['ROI'] == pytest.approx(3.8583333333333334)
    assert data.Date.min().date() == date(2024, 1, 5)
    assert data.Date.max().date() == date(2024, 7, 29)

def test_currency_duration_percent_cleaning(raw):
    raw['Acquisition_Cost'] = raw.Acquisition_Cost.astype(object)
    raw['Conversion_Rate'] = raw.Conversion_Rate.astype(object)
    raw.loc[0, 'Acquisition_Cost'] = '$1,420.50'
    raw.loc[0, 'Conversion_Rate'] = '12%'
    cleaned = clean_data(raw)
    assert cleaned.iloc[0].Spend == 1420.5
    assert cleaned.iloc[0].Duration_Days == 15
    assert cleaned.iloc[0].Conversions == 504

@pytest.mark.parametrize('column,value', [
    ('Date', '########'), ('Date', '2024-02-30'), ('Date', '01/05/2024'),
    ('Clicks', -1), ('Clicks', 1.5), ('Clicks', np.inf), ('Clicks', 999999),
    ('Acquisition_Cost', 'unknown'), ('Acquisition_Cost', -100),
    ('Conversion_Rate', 1.2), ('ROI', 'unknown'), ('Duration', '0 Days'),
    ('Campaign_ID', ''),
])
def test_invalid_values_are_not_silently_replaced(raw, column, value):
    raw[column] = raw[column].astype(object)
    raw.loc[0, column] = value
    with pytest.raises(DataValidationError):
        clean_data(raw)

def test_missing_columns(raw):
    with pytest.raises(DataValidationError, match='Missing required columns: Date'):
        clean_data(raw.drop(columns=['Date']))

def test_duplicate_campaign_ids(raw):
    raw.loc[1, 'Campaign_ID'] = raw.loc[0, 'Campaign_ID']
    with pytest.raises(DataValidationError, match='unique'):
        clean_data(raw)

def test_csv_excel_parity(raw):
    workbook = BytesIO()
    raw.to_excel(workbook, index=False)
    csv = raw.to_csv(index=False).encode()
    pd.testing.assert_frame_equal(clean_data(read_data(csv, 'a.csv')), clean_data(read_data(workbook.getvalue(), 'a.xlsx')))

def test_empty_upload_and_unreadable_file(raw):
    with pytest.raises(DataValidationError, match='no campaign rows'):
        clean_data(raw.head(0))
    with pytest.raises(DataValidationError, match='Cannot read'):
        read_data(b'\xff\xfe broken', 'bad.csv')

def test_zero_denominators(raw):
    one = raw.head(1).copy()
    one[['Clicks', 'Impressions', 'Acquisition_Cost']] = 0
    metrics = compute_metrics(clean_data(one))
    assert metrics['CTR'] is metrics['CPA'] is metrics['CPC'] is metrics['CVR'] is None
    assert metrics['Spend'] == metrics['Conversions'] == 0

def test_weighted_rates(raw):
    two = raw.head(2).copy()
    two['Clicks'] = [1, 90]
    two['Impressions'] = [10, 100]
    two['Acquisition_Cost'] = [10, 90]
    m = compute_metrics(clean_data(two))
    assert m['CTR'] == pytest.approx(91 / 110)
    assert m['CTR'] != pytest.approx((0.1 + 0.9) / 2)
    assert m['CPC'] == pytest.approx(100 / 91)

def test_filters_inclusive_and_empty(data):
    kwargs = dict(channels=['Facebook'], audiences=data.Target_Audience.unique(), goals=data.Campaign_Goal.unique(), segments=data.Customer_Segment.unique())
    one = apply_filters(data, date(2024, 1, 5), date(2024, 1, 5), **kwargs)
    assert one.Campaign_ID.tolist() == ['C001']
    assert apply_filters(data, data.Date.min(), data.Date.max(), **{**kwargs, 'channels': []}).empty
    assert apply_filters(data, data.Date.max(), data.Date.min(), **kwargs).empty

@pytest.mark.parametrize('frequency', ['Daily', 'Weekly', 'Monthly'])
def test_aggregation_reconciles_to_global_totals(data, frequency):
    grouped = time_metrics(data, frequency)
    platforms = aggregate_metrics(data, 'Channel_Used')
    for column in ['Spend', 'Clicks', 'Impressions', 'Conversions', 'Campaigns']:
        assert grouped[column].sum() == compute_metrics(data)[column]
        assert platforms[column].sum() == compute_metrics(data)[column]
    if frequency == 'Weekly':
        assert (grouped.Period.dt.dayofweek == 0).all()
    if frequency == 'Monthly':
        assert (grouped.Period.dt.day == 1).all()

def test_search_is_literal_case_insensitive(data):
    assert search_campaigns(data, 'c001').Campaign_ID.tolist() == ['C001']
    assert search_campaigns(data, 'alphamedia').Company.eq('AlphaMedia').all()
    assert search_campaigns(data, '[').empty

def test_clean_data_leaves_original_unchanged(raw):
    before = raw.copy(deep=True)
    clean_data(raw)
    pd.testing.assert_frame_equal(raw, before)

@pytest.mark.parametrize('header', ['Campaign_ID', ' Campaign_ID '])
def test_csv_campaign_ids_keep_leading_zeros(raw, header):
    sample = raw.head(2).copy()
    sample['Campaign_ID'] = ['001', '002']
    sample = sample.rename(columns={'Campaign_ID': header})
    cleaned = clean_data(read_data(sample.to_csv(index=False).encode(), 'campaigns.csv'))
    assert cleaned.Campaign_ID.tolist() == ['001', '002']
    assert search_campaigns(cleaned, '001').Campaign_ID.tolist() == ['001']


def test_channel_time_metrics_preserve_totals_and_missing_periods(data):
    from utils.metrics import channel_time_metrics
    totals = time_metrics(data, 'Daily')
    channels = channel_time_metrics(data, 'Daily', totals)
    assert len(channels) == len(totals) * data.Channel_Used.nunique()
    assert channels.Spend.sum() == compute_metrics(data)['Spend']
    assert channels.Clicks.isna().any()


def test_channel_comparison_is_bounded_before_expansion(data, monkeypatch):
    from utils import metrics
    totals = time_metrics(data, 'Daily')
    monkeypatch.setattr(metrics, 'MAX_CHANNEL_COMPARISON_POINTS', 1)
    with pytest.raises(metrics.ComparisonLimitError, match='select fewer channels'):
        metrics.channel_time_metrics(data, 'Daily', totals)
