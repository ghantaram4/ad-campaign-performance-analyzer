"""Ratios always use summed numerators and denominators."""
import pandas as pd

MAX_CHANNEL_COMPARISON_POINTS = 20_000


class ComparisonLimitError(ValueError):
    """A channel/date selection would produce too many plotted table rows."""

def safe_divide(numerator, denominator):
    return float(numerator / denominator) if denominator else None

def compute_metrics(df):
    spend = float(df.Spend.sum())
    clicks, impressions, conversions = (int(df[c].sum()) for c in ['Clicks', 'Impressions', 'Conversions'])
    return {
        'Campaigns': len(df), 'Spend': spend, 'Clicks': clicks, 'Impressions': impressions,
        'Conversions': conversions, 'CTR': safe_divide(clicks, impressions),
        'CPC': safe_divide(spend, clicks), 'CPA': safe_divide(spend, conversions),
        'CVR': safe_divide(conversions, clicks), 'ROI': float(df.ROI.mean()) if len(df) else None,
    }

def aggregate_metrics(df, column):
    rows = [{column: name, **compute_metrics(group)} for name, group in df.groupby(column, sort=True)]
    return pd.DataFrame(rows, columns=[column, 'Campaigns', 'Spend', 'Clicks', 'Impressions', 'Conversions', 'CTR', 'CPC', 'CPA', 'CVR', 'ROI'])

def time_metrics(df, frequency):
    if df.empty:
        return pd.DataFrame()
    groups = df.copy()
    # Weekly buckets begin on Monday; monthly buckets begin on the first.
    groups['Period'] = groups.Date.dt.to_period({'Daily': 'D', 'Weekly': 'W-SUN', 'Monthly': 'M'}[frequency]).dt.start_time
    return aggregate_metrics(groups, 'Period')


def channel_time_metrics(df, frequency, totals):
    # Bound the channel/date cross-product before allocating reindexed frames.
    if len(totals) * df.Channel_Used.nunique() > MAX_CHANNEL_COMPARISON_POINTS:
        raise ComparisonLimitError(
            'This channel comparison is too large to display. Choose Weekly or Monthly '
            'grouping, narrow the date range, or select fewer channels.')
    rows = []
    for name, group in df.groupby('Channel_Used'):
        periods = time_metrics(group, frequency).set_index('Period').reindex(totals.Period).reset_index()
        periods['Channel_Used'] = name
        rows.append(periods)
    return pd.concat(rows, ignore_index=True)

def campaign_metrics(df):
    out = df.copy()
    for col, numerator, denominator in [('CTR', 'Clicks', 'Impressions'), ('CPC', 'Spend', 'Clicks'), ('CPA', 'Spend', 'Conversions')]:
        out[col] = out[numerator] / out[denominator].replace(0, float('nan'))
    return out

def fmt_money(value):
    return 'N/A' if value is None or pd.isna(value) else f'${value:,.2f}'

def fmt_percent(value):
    return 'N/A' if value is None or pd.isna(value) else f'{value:.2%}'

def fmt_roi(value):
    return 'N/A' if value is None or pd.isna(value) else f'{value:.2f}%'
