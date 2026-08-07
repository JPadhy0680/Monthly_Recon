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

    # ✅ Flexible date column detection
    date_col = None
    for col in df.columns:
        if col in ["download date", "receipt date"]:
            date_col = col
            break

    if date_col is None:
        st.error(f"No valid date column found. Columns: {df.columns.tolist()}")
        st.stop()

    # ✅ Convert date column to datetime
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # ✅ Drop rows with invalid dates
    df = df.dropna(subset=[date_col])

    # ✅ Sort by date
    df = df.sort_values(by=[date_col])

    # ✅ Source column handling
    source_col = next((col for col in df.columns if col == "source"), None)

    if source_col:
        df[source_col] = df[source_col].astype(str).str.strip().str.upper()
    else:
        df["source"] = "UNKNOWN"
        source_col = "source"

    # ✅ Validity column handling
    validity_col = next((col for col in df.columns if col == "validity"), None)

    if validity_col:
        df[validity_col] = df[validity_col].astype(str).str.strip()

    summary_data = []

    # ✅ Process each unique Receipt/Download Date + Source separately
    date_source_pairs = (
        df[[date_col, source_col]]
        .drop_duplicates()
        .sort_values(by=[date_col, source_col])
        .reset_index(drop=True)
    )

    for idx, row in date_source_pairs.iterrows():
        current_date = row[date_col]
        source = row[source_col]

        # ✅ Filter only same date and same source
        subset = df[
            (df[date_col] == current_date) &
            (df[source_col] == source)
        ]

        # ✅ "No Report Received" check only for this specific date + source
        no_report_flag = subset.astype(str).apply(
            lambda col: col.str.contains("No Report Received", case=False, na=False)
        ).any().any()

        # ✅ Date logic
        if source == "MHRA":
            # Previous MHRA date only
            previous_mhra_dates = date_source_pairs[
                (date_source_pairs[source_col] == "MHRA") &
                (date_source_pairs[date_col] < current_date)
            ][date_col]

            if previous_mhra_dates.empty:
                if current_date.day_name() == "Monday":
                    from_date = current_date - pd.Timedelta(days=3)
                    to_date = current_date - pd.Timedelta(days=1)
                else:
                    from_date = current_date - pd.Timedelta(days=1)
                    to_date = current_date - pd.Timedelta(days=1)
            else:
                prev_date = previous_mhra_dates.max()
                from_date = prev_date
                to_date = current_date - pd.Timedelta(days=1)

        elif source in ["ADIS", "NA"]:
            weekday = current_date.weekday()
            from_date = current_date - pd.Timedelta(days=weekday)
            to_date = current_date

        else:
            from_date = None
            to_date = None

        # ✅ Summary calculation
        if no_report_flag:
            summary_data.append({
                "Receipt Date": current_date,
                "Source": source,
                "From": from_date,
                "To": to_date,
                "Total Number": "No Report Received",
                "Valid": "No Report Received",
                "Non-Valid": "No Report Received"
            })
        else:
            total = len(subset)

            if validity_col:
                validity_series = subset[validity_col].astype(str).str.strip().str.lower()
                valid = (validity_series == "valid").sum()
                non_valid = (validity_series == "non-valid").sum()
            else:
                valid = 0
                non_valid = 0

