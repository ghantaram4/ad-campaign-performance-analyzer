from html import escape
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CORAL = '#e76f61'
TEAL = '#238b87'
COLORS = {'Facebook': CORAL, 'Instagram': TEAL, 'Pinterest': '#b87850', 'Twitter': '#526b80'}
ACCENT = CORAL


def metric_label(metric):
    return {'Spend': 'Spend (USD)', 'Clicks': 'Clicks', 'Conversions': 'Estimated conversions',
            'ROI': 'Average reported ROI (%)', 'CTR': 'Click-through rate (%)',
            'CVR': 'Conversion rate (%)', 'CPC': 'Cost per click (USD)', 'CPA': 'Cost per acquisition (USD)'}[metric]


def value_format(metric):
    if metric in ['Spend', 'CPC', 'CPA']:
        return '$%{y:,.2f}'
    if metric in ['CTR', 'CVR']:
        return '%{y:.2%}'
    if metric == 'ROI':
        return '%{y:.2f}%'
    return '%{y:,.0f}'


def style_chart(fig, height=300):
    fig.update_layout(template='plotly_white', height=height,
                      font=dict(family='Arial', color='#38434a', size=12),
                      paper_bgcolor='white', plot_bgcolor='white',
                      margin=dict(l=12, r=12, t=40, b=12), bargap=.62,
                      legend=dict(orientation='h', y=1.18, x=0, font=dict(size=11)),
                      hovermode='x unified', hoverlabel=dict(bgcolor='white', font_size=12))
    fig.update_xaxes(showgrid=False, automargin=True, nticks=6, zeroline=False)
    fig.update_yaxes(gridcolor='#eee9e3', gridwidth=1, automargin=True, zeroline=False)
    return fig


def format_axis(fig, metric, **kwargs):
    fig.update_yaxes(title_text=metric_label(metric), title_font=dict(size=11), **kwargs)
    if metric in ['Spend', 'CPC', 'CPA']:
        fig.update_yaxes(tickprefix='$', **kwargs)
    elif metric in ['CTR', 'CVR']:
        fig.update_yaxes(tickformat='.1%', **kwargs)
    elif metric == 'ROI':
        fig.update_yaxes(ticksuffix='%', **kwargs)


def paired_chart(periods, first, second, channel=None):
    """Two explicit axes preserve units and readability without normalizing data."""
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    groups = periods.groupby('Channel_Used') if channel else [(None, periods)]
    for name, group in groups:
        for metric, secondary, color in [(first, False, CORAL), (second, True, TEAL)]:
            color = COLORS.get(name, ACCENT) if name else color
            label = f'{escape(str(name))} · {metric_label(metric)}' if name else metric_label(metric)
            fig.add_trace(go.Scatter(
                x=group.Period, y=group[metric], name=label, legendgroup=name,
                showlegend=not (channel and secondary), mode='lines+markers',
                connectgaps=False, line=dict(color=color, width=1.6, shape='linear',
                                             dash='dot' if channel and secondary else 'solid'),
                marker=dict(size=4),
                hovertemplate=metric_label(metric) + ': ' + value_format(metric) + '<extra></extra>'), secondary_y=secondary)
    format_axis(fig, first, secondary_y=False)
    format_axis(fig, second, secondary_y=True)
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return style_chart(fig, 320 if channel else 290)


def spend_conversion_chart(periods):
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_trace(go.Bar(x=periods.Period, y=periods.Spend, name='Spend (USD)', marker_color=CORAL,
                         opacity=.8, hovertemplate=value_format('Spend') + '<extra></extra>'), secondary_y=False)
    fig.add_trace(go.Scatter(x=periods.Period, y=periods.Conversions, name='Estimated conversions',
                             mode='lines+markers', marker=dict(size=4), connectgaps=False,
                             line=dict(color=TEAL, width=1.6, shape='linear'),
                             hovertemplate=value_format('Conversions') + '<extra></extra>'), secondary_y=True)
    format_axis(fig, 'Spend', secondary_y=False)
    format_axis(fig, 'Conversions', secondary_y=True)
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return style_chart(fig)


def platform_chart(platforms, metric):
    ordered = platforms.sort_values(metric, ascending=False)
    fig = go.Figure(go.Bar(x=[escape(str(name)) for name in ordered.Channel_Used], y=ordered[metric], width=.34,
                          marker_color=[COLORS.get(p, ACCENT) for p in ordered.Channel_Used],
                          hovertemplate='%{x}<br>' + value_format(metric) + '<extra></extra>'))
    format_axis(fig, metric)
    return style_chart(fig)


def trend_chart(periods, metric, channel=None):
    fig = go.Figure()
    groups = periods.groupby('Channel_Used') if channel else [(None, periods)]
    for name, group in groups:
        fig.add_trace(go.Scatter(x=group.Period, y=group[metric], name=escape(str(name)) if name else metric_label(metric),
                                 mode='lines+markers', connectgaps=False, marker=dict(size=4),
                                 line=dict(color=COLORS.get(name, ACCENT), width=1.6, shape='linear'),
                                 fill='tozeroy' if not channel and metric in ['Spend', 'Clicks', 'Conversions'] else None,
                                 fillcolor='rgba(231,111,97,.07)',
                                 hovertemplate=value_format(metric) + '<extra></extra>'))
    format_axis(fig, metric)
    return style_chart(fig, 300)


def funnel_chart(metrics):
    fig = go.Figure(go.Funnel(y=['Impressions', 'Clicks', 'Estimated conversions'],
                             x=[metrics['Impressions'], metrics['Clicks'], metrics['Conversions']],
                             textinfo='value+percent initial', textposition='outside',
                             marker=dict(color=['#efb2a5', CORAL, TEAL])))
    style_chart(fig, 280)
    fig.update_layout(margin=dict(l=140, r=80, t=20, b=20))
    return fig
