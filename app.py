import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="MHRA Summary Generator", layout="wide")

st.title("📊 MHRA Data Summary Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:

    # ✅ Read file FIRST
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # ✅ Clean columns
    df.columns = df.columns.str.strip()

    required_cols = ['Download Date', 'Source', 'MHRA ID', 'IRD', 'Validity']
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Missing columns: {missing}")
        st.stop()

    # ✅ Convert dates
    df['Download Date'] = pd.to_datetime(df['Download Date'], errors='coerce')
    df['IRD'] = pd.to_datetime(df['IRD'], errors='coerce')

    df = df.dropna(subset=['Download Date', 'IRD'])

    # ✅ ✅ NEW LOGIC STARTS HERE (correct placement)
    df = df.sort_values(by=['Source', 'Download Date'])

    summary_data = []

    for source, group in df.groupby('Source'):
        group = group.sort_values(by='Download Date')
        group = group.reset_index(drop=True)

        for i in range(len(group)):
            current_date = group.loc[i, 'Download Date']

            if i == 0:
                # First record logic
                if current_date.day_name() == 'Monday':
                    from_date = current_date - pd.Timedelta(days=3)
                    to_date = current_date - pd.Timedelta(days=1)
                else:
                    from_date = current_date - pd.Timedelta(days=1)
                    to_date = current_date - pd.Timedelta(days=1)
            else:
                prev_download_date = group.loc[i - 1, 'Download Date']
                from_date = prev_download_date
                to_date = current_date - pd.Timedelta(days=1)

            mask = (
                (group['IRD'] >= from_date) &
                (group['IRD'] <= to_date)
            )

            subset = group.loc[mask]

            summary_data.append({
                'Downloaded Date': current_date,
                'Source': source,
                'From': from_date,
                'To': to_date,
                'Total Number': len(subset),
                'Valid': (subset['Validity'] == 'Valid').sum(),
                'Non-Valid': (subset['Validity'] == 'Non-Valid').sum()
            })

    summary = pd.DataFrame(summary_data)

    # ✅ Format dates
    summary['Downloaded Date'] = summary['Downloaded Date'].dt.strftime('%d-%b-%y')
    summary['From'] = summary['From'].dt.strftime('%d-%b-%y')
    summary['To'] = summary['To'].dt.strftime('%d-%b-%y')

    st.success("✅ Summary Generated Successfully")
    st.dataframe(summary, use_container_width=True)

    # ✅ Download
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
