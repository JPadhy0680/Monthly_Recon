import streamlit as st
import pandas as pd

st.title("MHRA Data Summary Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
    except ImportError:
        st.error("openpyxl is not installed. Please install it using: pip install openpyxl")
        st.stop()

    df.columns = df.columns.str.strip()

    df['Download Date'] = pd.to_datetime(df['Download Date'], errors='coerce')
    df['IRD'] = pd.to_datetime(df['IRD'], errors='coerce')

    summary = df.groupby(['Download Date', 'Source']).agg(
        From=('IRD', 'min'),
        To=('IRD', 'max'),
        **{
            'Total Number': ('MHRA ID', 'count'),
            'Valid': ('Validity', lambda x: (x == 'Valid').sum()),
            'Non-Valid': ('Validity', lambda x: (x == 'Non-Valid').sum())
        }
    ).reset_index()

    summary['Download Date'] = summary['Download Date'].dt.strftime('%d-%b-%y')
    summary['From'] = summary['From'].dt.strftime('%d-%b-%y')
    summary['To'] = summary['To'].dt.strftime('%d-%b-%y')

    summary.rename(columns={'Download Date': 'Downloaded Date'}, inplace=True)

    st.dataframe(summary)
