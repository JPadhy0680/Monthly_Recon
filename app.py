import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Data Summary Generator", layout="wide")

st.title("📊 Data Summary Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file, engine="openpyxl")

    df.columns = df.columns.str.strip()

    df['Download Date'] = pd.to_datetime(df['Download Date'], errors='coerce')
    df = df.dropna(subset=['Download Date'])

    # ✅ SORT ONLY BY DATE (NOT SOURCE)
    df = df.sort_values(by=['Download Date'])

    summary_data = []

    # ✅ GROUP ONLY BY DOWNLOAD DATE
    unique_dates = df['Download Date'].drop_duplicates().reset_index(drop=True)

    for i in range(len(unique_dates)):

        current_date = unique_dates[i]

        subset = df[df['Download Date'] == current_date]

        # ✅ ✅ GLOBAL "NO REPORT RECEIVED" CHECK
        no_report_flag = subset.astype(str).apply(
            lambda col: col.str.contains("No Report Received", case=False, na=False)
        ).any().any()

        # ✅ PICK SOURCE (first value of that date)
        source = str(subset['Source'].iloc[0]).upper()

        # ✅ DATE LOGIC
        if source == "MHRA":

            if i == 0:
                if current_date.day_name() == 'Monday':
                    from_date = current_date - pd.Timedelta(days=3)
                    to_date = current_date - pd.Timedelta(days=1)
                else:
                    from_date = current_date - pd.Timedelta(days=1)
                    to_date = current_date - pd.Timedelta(days=1)
            else:
                prev_date = unique_dates[i - 1]
                from_date = prev_date
                to_date = current_date - pd.Timedelta(days=1)

        elif source in ["ADIS", "NA"]:
            weekday = current_date.weekday()
            from_date = current_date - pd.Timedelta(days=weekday)
            to_date = current_date

        else:
            from_date = None
            to_date = None

        # ✅ FINAL OUTPUT
        if no_report_flag:

            summary_data.append({
                'Downloaded Date': current_date,
                'Source': source,
                'From': from_date,
                'To': to_date,
                'Total Number': "No Report Received",
                'Valid': "No Report Received",
                'Non-Valid': "No Report Received"
            })

        else:

            total = len(subset)
            valid = (subset['Validity'] == 'Valid').sum()
            non_valid = (subset['Validity'] == 'Non-Valid').sum()

            summary_data.append({
                'Downloaded Date': current_date,
                'Source': source,
                'From': from_date,
                'To': to_date,
                'Total Number': total,
                'Valid': valid,
                'Non-Valid': non_valid
            })

    summary = pd.DataFrame(summary_data)

    # ✅ FORMAT DATES
    for col in ['Downloaded Date', 'From', 'To']:
        summary[col] = pd.to_datetime(summary[col], errors='coerce').dt.strftime('%d-%b-%y')

    st.dataframe(summary, use_container_width=True)

    # ✅ DOWNLOAD
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, index=False)

    output.seek(0)

    st.download_button(
        "⬇️ Download Excel",
        data=output,
        file_name="Summary_Output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
