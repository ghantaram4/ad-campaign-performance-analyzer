"""Ad Campaign Performance Analyzer. Run: python -m streamlit run app.py"""
from hashlib import sha256
from pathlib import Path
import pandas as pd
import streamlit as st
from utils.data_processing import CATEGORIES, DataValidationError, apply_filters, clean_data, read_data, search_campaigns
from utils.exports import download_csv, spreadsheet_safe_frame
from utils.metrics import ComparisonLimitError, aggregate_metrics, campaign_metrics, channel_time_metrics, compute_metrics, fmt_money, fmt_percent, fmt_roi, time_metrics
from utils.charts import funnel_chart, metric_label, paired_chart, platform_chart, spend_conversion_chart, trend_chart

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='Ad Campaign Performance Analyzer', page_icon='📊', layout='wide')

CSS = '''
<style>
.block-container {padding-top: 1.6rem; max-width: 1600px;}
h1 {font-size: 2.05rem !important; letter-spacing: -.065rem;}
h2, h3 {letter-spacing: -.025rem;}
[data-testid="stMetric"] {background: white; padding: 1.05rem 1.15rem; border: 1px solid #e8e1da; border-radius: 14px;}
[data-testid="stMetricValue"] {font-size: 1.7rem;}
[data-testid="stMetricLabel"] {color: #746f69;}
[data-testid="stSidebar"] {border-right: 1px solid #e8e1da;}
[data-testid="stTabs"] [role="tablist"] {gap: 1.5rem; border-bottom: 1px solid #e8e1da; margin-bottom: 1.2rem;}
[data-testid="stTabs"] [role="tab"] {font-size: 15px; padding-bottom: 14px;}
.eyebrow {font-size: .76rem; font-weight: 700; color: #e76f61; letter-spacing: .12rem; margin-bottom: .4rem;}
[data-testid="stVerticalBlockBorderWrapper"] > div, [data-testid="stLayoutWrapper"]:has(> [data-testid="stVerticalBlock"]) {background: white; border-radius: 12px;}
[data-testid="stSidebar"] {background: #202b33; color: #f7f3ed;}
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] label, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color: #e7e1da;}
@media (max-width: 800px) {
  .block-container {padding: 1rem;}
  [data-testid="stHorizontalBlock"] {flex-wrap: wrap;}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {min-width: min(100%, 320px); flex: 1 1 320px;}
}
</style>
'''

def load_data(content, filename):
    return clean_data(read_data(content, filename))

def reset_filters(df):
    st.session_state['date_from'] = df.Date.min().date()
    st.session_state['date_to'] = df.Date.max().date()
    for col in CATEGORIES:
        st.session_state['filter_' + col] = sorted(df[col].unique().tolist())

def render_sidebar(df):
    st.sidebar.divider()
    st.sidebar.subheader('Global filters')
    st.sidebar.caption('Every view uses these selections. Clearing a selection returns no campaigns.')
    st.sidebar.button('Reset filters', on_click=reset_filters, args=(df,), width='stretch')
    low, high = df.Date.min().date(), df.Date.max().date()
    start = st.sidebar.date_input('From', min_value=low, max_value=high, key='date_from')
    end = st.sidebar.date_input('To', min_value=low, max_value=high, key='date_to')
    selected = {}
    labels = {'Channel_Used': 'Channel', 'Target_Audience': 'Target audience', 'Campaign_Goal': 'Campaign goal', 'Customer_Segment': 'Customer segment'}
    for col in CATEGORIES:
        selected[col] = st.sidebar.multiselect(labels[col], sorted(df[col].unique()), key='filter_' + col)
    if start > end:
        st.sidebar.error('From date must be on or before To date.')
    return apply_filters(df, start, end, selected['Channel_Used'], selected['Target_Audience'], selected['Campaign_Goal'], selected['Customer_Segment'])

def show_table(df, key):
    labels = {'Campaign_ID': 'Campaign', 'Company': 'Company', 'Channel_Used': 'Channel', 'Campaign_Goal': 'Goal',
              'Target_Audience': 'Audience', 'Customer_Segment': 'Segment', 'Campaigns': 'Campaigns'}
    config = {name: st.column_config.TextColumn(label) for name, label in labels.items() if name != 'Campaigns'}
    for col in ['Spend', 'CPC', 'CPA']:
        config[col] = st.column_config.NumberColumn(metric_label(col), format='$%.2f')
    for col in ['CTR', 'CVR', 'Conversion_Rate']:
        config[col] = st.column_config.NumberColumn('Conversion rate (%)' if col == 'Conversion_Rate' else metric_label(col), format='percent')
    config['ROI'] = st.column_config.NumberColumn('Reported ROI (%)', format='%.2f%%', help='Reported percentage points, following the solution kit. Not recomputed from revenue.')
    config['Date'] = st.column_config.DateColumn('Recorded date', format='YYYY-MM-DD')
    for col in ['Clicks', 'Impressions', 'Conversions', 'Campaigns', 'Duration_Days']:
        config[col] = st.column_config.NumberColumn('Estimated conversions' if col == 'Conversions' else col.replace('_', ' '), format='localized')
    st.dataframe(spreadsheet_safe_frame(df), column_config=config, hide_index=True, width='stretch', key=key)

def render_pairs(periods, prefix, split=False):
    for column, title, first, second in zip(st.columns(2),
            ['Clicks vs estimated conversions', 'CTR vs conversion rate'],
            ['Clicks', 'CTR'], ['Conversions', 'CVR']):
        with column, st.container(border=True):
            st.subheader(title)
            st.caption('Left axis: ' + metric_label(first) + '. Right axis: ' + metric_label(second) + '.')
            if split:
                st.caption('Channel colours stay consistent; dotted lines show the right-axis metric.')
            st.plotly_chart(paired_chart(periods, first, second, channel=split),
                            width='stretch', key=f'{prefix}_{first}_{second}')


def render_overview(df):
    m = compute_metrics(df)
    for col, label, value, help_text in zip(st.columns(5),
            ['Total spend', 'Clicks', 'Estimated conversions', 'Click-through rate', 'Average reported ROI'],
            [fmt_money(m['Spend']), f"{m['Clicks']:,}", f"{m['Conversions']:,}", fmt_percent(m['CTR']), fmt_roi(m['ROI'])],
            ['Total campaign spend in USD.', 'Total campaign clicks.', 'Sum of round(clicks × conversion rate), per campaign.', 'Total clicks ÷ total impressions.', 'Arithmetic mean of the supplied ROI values, in percentage points.']):
        col.metric(label, value, help=help_text)
    st.write('')
    frequency = st.selectbox('Group overview dates by', ['Daily', 'Weekly', 'Monthly'], index=1, key='overview_frequency')
    periods = time_metrics(df, frequency)
    with st.container(border=True):
        st.subheader('Spend and conversion outcomes')
        st.caption(f'{frequency} totals for whole campaigns grouped by recorded date. Spend uses the left axis; estimated conversions use the right.')
        st.plotly_chart(spend_conversion_chart(periods), width='stretch', key='overview_trend')
    render_pairs(periods, 'overview')
    left, right = st.columns([2, 1])
    with left, st.container(border=True):
        st.subheader('Top 5 campaigns by reported ROI')
        show_table(df.nlargest(5, 'ROI')[['Campaign_ID', 'Company', 'Channel_Used', 'ROI', 'Spend', 'Conversions']], 'top5')
    with right, st.container(border=True):
        st.subheader('Acquisition efficiency')
        st.metric('Cost per click', fmt_money(m['CPC']))
        st.metric('Cost per acquisition', fmt_money(m['CPA']))
        st.metric('Conversion rate', fmt_percent(m['CVR']))

def render_platforms(df):
    platforms = aggregate_metrics(df, 'Channel_Used')
    st.subheader('Compare channel performance')
    metric = st.selectbox('Comparison metric', ['Spend', 'Conversions', 'Clicks', 'ROI', 'CTR', 'CPC', 'CPA', 'CVR'], format_func=metric_label, key='platform_metric')
    st.plotly_chart(platform_chart(platforms, metric), width='stretch', key='platform_chart')
    st.caption('CTR, CVR, CPC and CPA use totals within each channel. ROI is the mean reported campaign value. N/A means a zero denominator.')
    show_table(platforms, 'platform_summary')
    download_csv('Download channel summary', platforms, 'channel_summary.csv', key='platform_export')

def render_campaigns(df):
    st.subheader('Explore individual campaigns')
    query = st.text_input('Search campaigns', placeholder='Campaign ID, company, channel, goal, audience or segment', key='campaign_search')
    matches = search_campaigns(df, query)
    st.caption(f'{len(matches):,} of {len(df):,} globally filtered campaigns match this search. Search affects this tab only.')
    if matches.empty:
        st.info('No campaigns match your search. Try a different campaign ID or company name.')
        return
    details = campaign_metrics(matches)
    columns = ['Campaign_ID', 'Company', 'Channel_Used', 'Campaign_Goal', 'Target_Audience', 'Customer_Segment', 'Date', 'Spend', 'Impressions', 'Clicks', 'Conversions', 'CTR', 'CPC', 'CPA', 'ROI', 'Duration_Days']
    show_table(details[columns], 'campaign_details')
    st.caption('Click a column header to sort. Monetary values are in USD; ROI is in percentage points.')
    download_csv('Download campaign results', details[columns], 'campaign_results.csv', key='campaign_export')
    with st.container(border=True):
        st.subheader('Acquisition funnel')
        st.caption('For the campaigns shown in the table. Conversions are estimated from the supplied conversion rates.')
        m = compute_metrics(matches)
        for col, key in zip(st.columns(3), ['Impressions', 'Clicks', 'Conversions']):
            col.metric('Estimated conversions' if key == 'Conversions' else key, f'{m[key]:,}')
        st.plotly_chart(funnel_chart(m), width='stretch', key='campaign_funnel')

def render_trends(df):
    st.subheader('Performance by recorded campaign date')
    c1, c2, c3 = st.columns(3)
    metric = c1.selectbox('Trend metric', ['Spend', 'Clicks', 'Conversions', 'ROI', 'CTR', 'CPC', 'CPA', 'CVR'], format_func=metric_label, key='trend_metric')
    frequency = c2.selectbox('Group dates by', ['Daily', 'Weekly', 'Monthly'], index=1, key='trend_frequency')
    split = c3.toggle('Compare channels', key='trend_split')
    totals = time_metrics(df, frequency)
    if split:
        try:
            chart_data = channel_time_metrics(df, frequency, totals)
        except ComparisonLimitError as exc:
            st.info(str(exc))
            return
    else:
        chart_data = totals
    with st.container(border=True):
        st.plotly_chart(trend_chart(chart_data, metric, channel=split or None), width='stretch', key='time_chart')
    render_pairs(chart_data, 'time', split)

    st.caption('These are full campaign outcomes grouped by the recorded date, not daily delivery. Periods without recorded campaigns are omitted; gaps in channel series are left blank. Weeks start Monday.')
    show_table(chart_data.rename(columns={'Period': 'Date'}), 'time_summary')
    download_csv('Download time summary', chart_data, 'time_summary.csv', key='time_export')

def main():
    st.markdown(CSS, unsafe_allow_html=True)
    st.sidebar.markdown('### Campaign Analyzer')
    st.sidebar.caption('Campaign CSV → marketing insights')
    st.sidebar.caption('Public demo: upload only sample or non-confidential campaign data.')
    upload = st.sidebar.file_uploader('Upload campaign data', type=['csv', 'xlsx'], key='data_upload', help='CSV/XLSX, up to 10 MB and 10,000 campaigns. Excel formulas are not accepted.')
    try:
        filename = upload.name if upload is not None else 'social_media_advertising_sample.csv'
        content = upload.getvalue() if upload is not None else (ROOT / 'data' / filename).read_bytes()
        fingerprint = sha256(content).hexdigest()
        source_key = (fingerprint, Path(filename).suffix.lower())
        if st.session_state.get('loaded_source_key') != source_key:
            st.session_state.pop('loaded_data', None)
            st.session_state.pop('loaded_source_key', None)
            parsed = load_data(content, filename)
            st.session_state['loaded_data'] = parsed
            st.session_state['loaded_source_key'] = source_key
        df = st.session_state['loaded_data']
    except DataValidationError as exc:
        st.error(str(exc))
        st.info('Fix the file and upload it again. The expected schema is documented in README.md.')
        st.stop()
    except Exception:
        st.session_state.pop('loaded_data', None)
        st.session_state.pop('loaded_source_key', None)
        st.error('Unable to load campaign data. Check the file format and documented limits.')
        st.stop()
    if st.session_state.get('source_fingerprint') != fingerprint:
        reset_filters(df)
        st.session_state['source_fingerprint'] = fingerprint
        st.session_state['campaign_search'] = ''
    st.sidebar.caption(f"{'Uploaded data' if upload is not None else 'Bundled dataset'}: {len(df)} campaigns")
    filtered = render_sidebar(df)
    st.markdown('<div class="eyebrow">MARKETING ANALYTICS</div>', unsafe_allow_html=True)
    st.title('Ad Campaign Performance Analyzer')
    st.caption('Compare spend, conversion outcomes and reported ROI across your advertising channels.')
    st.caption(f"Showing {len(filtered):,} of {len(df):,} campaigns. Source dates: {df.Date.min():%b %d, %Y} – {df.Date.max():%b %d, %Y}. Currency: USD.")
    with st.expander('Metric definitions and data notes'):
        st.markdown('**Spend:** sum of Acquisition_Cost. **Estimated conversions:** sum of rounded Clicks × Conversion_Rate. '
                    '**CTR:** total clicks ÷ total impressions. **CPC:** total spend ÷ total clicks. '
                    '**CPA:** total spend ÷ estimated conversions. **CVR:** estimated conversions ÷ clicks. '
                    '**Average reported ROI:** arithmetic mean of ROI, displayed as percentage points following the solution kit. '
                    'A value of 3.2 is displayed as 3.20%. The workbook does not define a revenue formula, so ROI is not recomputed. '
                    '**N/A:** a ratio has a zero denominator. Each row is a whole campaign, and dates group whole campaign outcomes.')
        st.caption('Validation checks required columns, unique campaign IDs, ISO dates, valid counts, spend, duration and conversion rates. Source records are not silently dropped or replaced.')
    tabs = st.tabs(['Overview', 'Platform Comparison', 'Campaign Details', 'Time Series'])
    for tab, renderer in zip(tabs, [render_overview, render_platforms, render_campaigns, render_trends]):
        with tab:
            if filtered.empty:
                st.info('No data for selected filters. Widen the date range, choose more categories, or reset filters.')
            else:
                renderer(filtered)

if __name__ == '__main__':
    main()
