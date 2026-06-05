import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="MHRA Summary Generator", layout="wide")

st.title("📊 MHRA Data Summary Generator")

st.markdown("Upload your Excel file to generate summary output.")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:

    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    df.columns = df.columns.str.strip()

    expected_cols = ['Download Date', 'Source', 'MHRA ID', 'IRD', 'Validity']
    missing = [col for col in expected_cols if col not in df.columns]

    if missing:
        st.error(f"Missing columns: {missing}")
        st.stop()

    df['Download Date'] = pd.to_datetime(df['Download Date'], errors='coerce')
    df['IRD'] = pd.to_datetime(df['IRD'], errors='coerce')

    df = df.dropna(subset=['Download Date', 'IRD'])

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

    st.success("✅ Summary Generated Successfully")
    st.dataframe(summary, use_container_width=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        summary.to_excel(writer, index=False, sheet_name='Summary')

    output.seek(0)

    st.download_button(
        label="⬇️ Download Summary Excel",
        data=output,
        file_name="MHRA_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
