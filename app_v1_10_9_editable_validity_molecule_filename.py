import streamlit as st
import pandas as pd
from io import BytesIO

st.title("MHRA Data Summary Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    # Read Excel file
    df = pd.read_excel(uploaded_file, engine="openpyxl")

    # Standardize column names (remove spaces issues)
    df.columns = df.columns.str.strip()

    # Convert dates
    df['Download Date'] = pd.to_datetime(df['Download Date'], errors='coerce')
    df['IRD'] = pd.to_datetime(df['IRD'], errors='coerce')

    # Create summary
    summary = df.groupby(['Download Date', 'Source']).agg(
        From_Date=('IRD', 'min'),
        To_Date=('IRD', 'max'),
        Total_Number=('MHRA ID', 'count'),
        Valid=('Validity', lambda x: (x == 'Valid').sum()),
        Non_Valid=('Validity', lambda x: (x == 'Non-Valid').sum())
    ).reset_index()

    # Format dates
    summary['Download Date'] = summary['Download Date'].dt.strftime('%d-%b-%y')
    summary['From_Date'] = summary['From_Date'].dt.strftime('%d-%b-%y')
    summary['To_Date'] = summary['To_Date'].dt.strftime('%d-%b-%y')

    # Rename columns to match expected output
    summary.rename(columns={
        'Download Date': 'Downloaded Date',
        'From_Date': 'From',
        'To_Date': 'To',
        'Total_Number': 'Total Number',
        'Non_Valid': 'Non-Valid'
    }, inplace=True)

    st.subheader("Summary Output")
    st.dataframe(summary)

    # Convert to Excel for download
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        summary.to_excel(writer, index=False, sheet_name='Summary')

    output.seek(0)

    st.download_button(
        label="Download Summary Excel",
        data=output,
        file_name="MHRA_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
