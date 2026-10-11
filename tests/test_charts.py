import pandas as pd
import pytest
from utils.charts import COLORS, paired_chart, platform_chart, trend_chart
from utils.metrics import time_metrics


@pytest.mark.parametrize('frequency', ['Daily', 'Weekly', 'Monthly'])
def test_grouped_rates_use_totals(data, frequency):
    periods = time_metrics(data, frequency)
    assert periods.CTR.tolist() == pytest.approx((periods.Clicks / periods.Impressions).tolist())
    assert periods.CVR.tolist() == pytest.approx((periods.Conversions / periods.Clicks).tolist())
    for first, second in [('Clicks', 'Conversions'), ('CTR', 'CVR')]:
        fig = paired_chart(periods, first, second)
        assert list(fig.data[0].y) == periods[first].tolist()
        assert list(fig.data[1].y) == periods[second].tolist()
        assert fig.data[0].yaxis == 'y'
        assert fig.data[1].yaxis == 'y2'
        assert len(fig.data[0].x) == len(periods)


def test_channel_gaps_and_colours_are_preserved(data):
    periods = time_metrics(data, 'Weekly')
    channel = time_metrics(data[data.Channel_Used == 'Facebook'], 'Weekly')
    channel = channel.set_index('Period').reindex(periods.Period).reset_index()
    channel['Channel_Used'] = 'Facebook'
    fig = paired_chart(channel, 'Clicks', 'Conversions', channel=True)
    for trace in fig.data:
        assert trace.connectgaps is False
        assert trace.line.color == COLORS['Facebook']
        assert sum(pd.isna(trace.y)) == channel.Clicks.isna().sum()
    assert fig.data[1].line.dash == 'dot'
    assert trend_chart(channel, 'CTR', channel=True).data[0].fill is None


def test_channel_bars_are_slim(data):
    from utils.metrics import aggregate_metrics
    fig = platform_chart(aggregate_metrics(data, 'Channel_Used'), 'CTR')
    assert fig.data[0].width == .34
    assert fig.layout.yaxis.tickformat == '.1%'
