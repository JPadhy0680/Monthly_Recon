import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="MHRA Summary Generator", layout="wide")

st.title("📊 MHRA Data Summary Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:

    # ✅ Read Excel
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # ✅ Clean column names
    df.columns = df.columns.str.strip()

    required_cols = ['Download Date', 'Source', 'MHRA ID', 'IRD', 'Validity']
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        st.error(f"Missing columns: {missing}")
        st.stop()

    # ✅ Convert to datetime
    df['Download Date'] = pd.to_datetime(df['Download Date'], errors='coerce')
    df['IRD'] = pd.to_datetime(df['IRD'], errors='coerce')

    df = df.dropna(subset=['Download Date'])

    # ✅ Sort data
    df = df.sort_values(by=['Source', 'Download Date'])

    summary_data = []

    # ✅ Process per Source
    for source, group in df.groupby('Source'):

        group = group.sort_values(by='Download Date')

        # ✅ Unique Download Dates (important)
        unique_dates = (
            group['Download Date']
            .drop_duplicates()
            .sort_values()
            .reset_index(drop=True)
        )

        for i in range(len(unique_dates)):
            current_date = unique_dates[i]

            # ✅ From-To Logic
            if i == 0:
                if current_date.day_name() == 'Monday':
                    from_date = current_date - pd.Timedelta(days=3)  # Friday
                    to_date = current_date - pd.Timedelta(days=1)    # Sunday
                else:
                    from_date = current_date - pd.Timedelta(days=1)
                    to_date = current_date - pd.Timedelta(days=1)
            else:
                prev_date = unique_dates[i - 1]
                from_date = prev_date
                to_date = current_date - pd.Timedelta(days=1)

            # ✅ ✅ CORRECT COUNTING LOGIC (Your requirement)
            subset = group[group['Download Date'] == current_date]

            total_count = len(subset)
            valid_count = (subset['Validity'] == 'Valid').sum()
            non_valid_count = (subset['Validity'] == 'Non-Valid').sum()

            summary_data.append({
                'Downloaded Date': current_date,
                'Source': source,
                'From': from_date,
                'To': to_date,
                'Total Number': total_count,
                'Valid': valid_count,
                'Non-Valid': non_valid_count
            })

    # ✅ Create summary
    summary = pd.DataFrame(summary_data)

    # ✅ Format dates
    summary['Downloaded Date'] = summary['Downloaded Date'].dt.strftime('%d-%b-%y')
    summary['From'] = summary['From'].dt.strftime('%d-%b-%y')
    summary['To'] = summary['To'].dt.strftime('%d-%b-%y')

    st.success("✅ Summary Generated Successfully")
    st.dataframe(summary, use_container_width=True)

    # ✅ Download Excel
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
