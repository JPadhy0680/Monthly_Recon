import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Data Summary Generator", layout="wide")
st.title("📊 Data Summary Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, engine="openpyxl")

    # ✅ Clean column names
    df.columns = df.columns.str.strip().str.lower()

    # ✅ Flexible column detection (supports both old + new headers)
    date_col = None
    for col in df.columns:
        if col in ['download date', 'receipt date']:
            date_col = col
            break

    if date_col is None:
        st.error(f"No valid date column found. Columns: {df.columns.tolist()}")
        st.stop()

    # ✅ Convert to datetime
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # ✅ Drop invalid dates
    df = df.dropna(subset=[date_col])

    # ✅ Sort by date
    df = df.sort_values(by=[date_col])

    summary_data = []

    # ✅ Unique dates
    unique_dates = df[date_col].drop_duplicates().reset_index(drop=True)

    for i in range(len(unique_dates)):
        current_date = unique_dates[i]
        subset = df[df[date_col] == current_date]

        # ✅ Global "No Report Received" check
        no_report_flag = subset.astype(str).apply(
            lambda col: col.str.contains("No Report Received", case=False, na=False)
        ).any().any()

        # ✅ Normalize Source column
        source_col = next((col for col in df.columns if col == 'source'), None)
        source = str(subset[source_col].iloc[0]).upper() if source_col else "UNKNOWN"

        # ✅ Date logic
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

        # ✅ Validity column handling
        validity_col = next((col for col in df.columns if col == 'validity'), None)

        if no_report_flag:
            summary_data.append({
                'Receipt Date': current_date,
                'Source': source,
                'From': from_date,
                'To': to_date,
                'Total Number': "No Report Received",
                'Valid': "No Report Received",
                'Non-Valid': "No Report Received"
            })
        else:
            total = len(subset)
            valid = (subset[validity_col] == 'Valid').sum() if validity_col else 0
            non_valid = (subset[validity_col] == 'Non-Valid').sum() if validity_col else 0

            summary_data.append({
                'Receipt Date': current_date,
                'Source': source,
                'From': from_date,
                'To': to_date,
                'Total Number': total,
                'Valid': valid,
                'Non-Valid': non_valid
            })

    summary = pd.DataFrame(summary_data)

    # ✅ Format dates
    for col in ['Receipt Date', 'From', 'To']:
        summary[col] = pd.to_datetime(summary[col], errors='coerce').dt.strftime('%d-%b-%y')

    # ✅ Show table
    st.dataframe(summary, use_container_width=True)

    # ✅ Download
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
