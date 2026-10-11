from datetime import date
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'

@pytest.fixture
def app():
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not at.exception
    return at

def test_default_app_has_four_views_and_real_metrics(app):
    assert [t.label for t in app.tabs] == ['Overview', 'Platform Comparison', 'Campaign Details', 'Time Series']
    assert app.date_input(key='date_from').value == date(2024, 1, 5)
    assert app.date_input(key='date_to').value == date(2024, 7, 29)
    assert app.metric[0].value == '$29,490.00'
    assert app.metric[1].value == '304,450'
    assert app.metric[2].value == '61,361'
    assert app.metric[4].value == '3.86%'

def test_channel_filter_updates_every_view(app):
    app.multiselect(key='filter_Channel_Used').set_value(['Facebook']).run()
    assert not app.exception
    assert app.metric[0].value == '$8,570.00'
    tables = [item.value for item in app.dataframe]
    assert tables[0].Channel_Used.eq('Facebook').all()
    assert tables[1].Channel_Used.tolist() == ['Facebook']
    assert len(tables[2]) == 15
    assert tables[3].Spend.sum() == 8570

def test_empty_filter_has_message_in_all_views_and_reset_restores(app):
    app.multiselect(key='filter_Channel_Used').set_value([]).run()
    assert not app.exception
    assert len(app.info) == 4
    assert not app.metric
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == '$29,490.00'

def test_inverted_date_range_does_not_crash(app):
    app.date_input(key='date_from').set_value(date(2024, 7, 29))
    app.date_input(key='date_to').set_value(date(2024, 1, 5)).run()
    assert not app.exception
    assert 'From date' in app.error[0].value
    assert len(app.info) == 4

def test_local_campaign_search_updates_table_and_funnel_only(app):
    app.text_input(key='campaign_search').set_value('C001').run()
    assert not app.exception
    assert app.metric[0].value == '$29,490.00'
    assert app.dataframe[2].value.Campaign_ID.tolist() == ['C001']
    assert app.metric[-1].value == '504'
    app.text_input(key='campaign_search').set_value('missing-campaign').run()
    assert not app.exception
    assert any('No campaigns match' in item.value for item in app.info)

@pytest.mark.parametrize('key,choice', [('filter_Target_Audience', '18-25'), ('filter_Campaign_Goal', 'Sales'), ('filter_Customer_Segment', 'Technology')])
def test_other_global_filters_update_campaign_table(app, key, choice):
    app.multiselect(key=key).set_value([choice]).run()
    assert not app.exception
    assert app.dataframe[2].value[key.removeprefix('filter_')].eq(choice).all()

def test_all_trend_frequencies_and_channel_comparison(app):
    app.toggle(key='trend_split').set_value(True)
    for frequency in ['Daily', 'Weekly', 'Monthly']:
        app.selectbox(key='trend_frequency').set_value(frequency).run()
        assert not app.exception
        assert set(app.dataframe[-1].value.Channel_Used) == {'Facebook', 'Instagram', 'Twitter', 'Pinterest'}
    for metric in ['ROI', 'CPA', 'CTR']:
        app.selectbox(key='trend_metric').set_value(metric).run()
        app.selectbox(key='platform_metric').set_value(metric).run()
        assert not app.exception

def test_weekly_initial_view_and_paired_charts(app):
    assert app.selectbox(key='trend_frequency').value == 'Weekly'
    assert app.selectbox(key='overview_frequency').value == 'Weekly'
    for frequency in ['Daily', 'Monthly']:
        app.selectbox(key='overview_frequency').set_value(frequency).run()
        assert not app.exception

def test_source_state_is_session_local():
    one = AppTest.from_file(str(APP), default_timeout=30).run()
    two = AppTest.from_file(str(APP), default_timeout=30).run()
    one.session_state['loaded_data'].loc[0, 'Company'] = 'SESSION_ONE_ONLY'
    assert not two.session_state['loaded_data'].Company.eq('SESSION_ONE_ONLY').any()
    assert one.session_state['loaded_data'] is not two.session_state['loaded_data']


def test_large_channel_comparison_reports_limit_without_breaking_other_views(app, monkeypatch):
    from utils import metrics
    monkeypatch.setattr(metrics, 'MAX_CHANNEL_COMPARISON_POINTS', 1)
    app.toggle(key='trend_split').set_value(True).run()
    assert not app.exception
    assert any('channel comparison is too large' in item.value for item in app.info)
    assert app.metric[0].value == '$29,490.00'
    assert len(app.dataframe) == 3
    app.toggle(key='trend_split').set_value(False).run()
    assert not app.exception
    assert len(app.dataframe) == 4
