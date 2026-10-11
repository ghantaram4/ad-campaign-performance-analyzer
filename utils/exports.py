"""Spreadsheet-safe exports without changing stored data or numeric analytics."""
import pandas as pd


def safe_text(value):
    if isinstance(value, str):
        # Leading whitespace/control characters can hide a formula prefix.
        prefix = value.lstrip(''.join(chr(i) for i in range(33)) + '\ufeff')
        if prefix.startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')):
            return "'" + value
    return value


def spreadsheet_safe_frame(df):
    out = df.copy()
    for column in out.columns:
        if pd.api.types.is_object_dtype(out[column]) or pd.api.types.is_string_dtype(out[column]):
            out[column] = out[column].map(safe_text)
    return out


def export_csv(df):
    return spreadsheet_safe_frame(df).to_csv(index=False, date_format='%Y-%m-%d').encode('utf-8')


def download_csv(label, df, filename, key=None):
    """Keep exports in the session's browser instead of shared /media endpoints.

    Only base64 CSV bytes and escaped labels enter this fixed iframe document.
    The browser saves a data URL; no uploaded string becomes markup or script.
    """
    from base64 import b64encode
    from html import escape
    import streamlit as st

    encoded = b64encode(export_csv(df)).decode('ascii')
    document = f'''<!doctype html><html><head><meta charset="utf-8">
    <style>body {{margin:0;font-family:Arial,sans-serif;}}
    a {{display:inline-block;background:#fff;color:#202b33;border:1px solid #d8d1c9;
        border-radius:8px;padding:10px 14px;font-size:14px;text-decoration:none;}}
    a:hover {{border-color:#e76f61;color:#e76f61;}}
    a:focus-visible {{outline:2px solid #e76f61;outline-offset:2px;}}</style></head>
    <body><a download="{escape(filename, quote=True)}"
    href="data:text/csv;base64,{encoded}">{escape(label)}</a></body></html>'''
    st.iframe(document, height=48, alt=label)
