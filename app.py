import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Data Summary Generator", layout="wide")

st.title("📊 Data Summary Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

        st.success("File uploaded successfully.")

        if df.empty:
            st.error("The uploaded Excel file is empty.")
            st.stop()

        # Clean column names
        df.columns = df.columns.astype(str).str.strip().str.lower()

        st.write("Detected columns:", df.columns.tolist())

        # Flexible date column detection
        possible_date_cols = [
            "download date",
            "receipt date",
            "downloaded date",
            "date of receipt",
            "receiptdate",
            "download_date",
            "receipt_date"
        ]

        date_col = None
        for col in df.columns:
            if col in possible_date_cols:
                date_col = col
                break

        if date_col is None:
            st.error("No valid date column found.")
            st.write("Available columns:", df.columns.tolist())
            st.stop()

        st.info(f"Using date column: {date_col}")

        # Convert date column to datetime
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

        invalid_date_count = df[date_col].isna().sum()

        if invalid_date_count > 0:
            st.warning(f"{invalid_date_count} row(s) have invalid or blank dates and will be ignored.")

        # Drop rows with invalid dates
        df = df.dropna(subset=[date_col])

        if df.empty:
            st.error("No valid rows found after date conversion. Please check the date format in Excel.")
            st.stop()

        # Sort by date
        df = df.sort_values(by=[date_col])

        # Source column handling
        source_col = next((col for col in df.columns if col == "source"), None)

        if source_col:
            df[source_col] = df[source_col].astype(str).str.strip().str.upper()
        else:
            st.warning("No Source column found. Source will be marked as UNKNOWN.")
            df["source"] = "UNKNOWN"
            source_col = "source"

        # Replace blank source values
        df[source_col] = df[source_col].replace(["", "NAN", "NONE"], "UNKNOWN")

        # Validity column handling
        validity_col = next((col for col in df.columns if col == "validity"), None)

        if validity_col:
            df[validity_col] = df[validity_col].astype(str).str.strip()
        else:
            st.warning("No Validity column found. Valid and Non-Valid counts will be zero.")

        summary_data = []

        # Process each unique Date + Source separately
        date_source_pairs = (
            df[[date_col, source_col]]
            .drop_duplicates()
            .sort_values(by=[date_col, source_col])
            .reset_index(drop=True)
        )

        if date_source_pairs.empty:
            st.error("No date and source combinations found.")
            st.stop()

        for idx, row in date_source_pairs.iterrows():
            current_date = row[date_col]
            source = row[source_col]

            subset = df[
                (df[date_col] == current_date) &
                (df[source_col] == source)
            ]

            if subset.empty:
                continue

            # No Report Received check only for same date + same source
            no_report_flag = subset.astype(str).apply(
                lambda col: col.str.contains("No Report Received", case=False, na=False)
            ).any().any()

            # Date logic
            if source == "MHRA":
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

                summary_data.append({
                    "Receipt Date": current_date,
                    "Source": source,
                    "From": from_date,
                    "To": to_date,
                    "Total Number": total,
                    "Valid": valid,
                    "Non-Valid": non_valid
                })

        if not summary_data:
            st.error("No summary records were generated.")
            st.stop()

        summary = pd.DataFrame(summary_data)

        # Format dates
        for col in ["Receipt Date", "From", "To"]:
            summary[col] = pd.to_datetime(summary[col], errors="coerce").dt.strftime("%d-%b-%y")

        summary = summary.fillna("")

        st.subheader("Summary Output")
        st.dataframe(summary, use_container_width=True)

        # Download Excel
        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            summary.to_excel(writer, index=False, sheet_name="Summary")

        output.seek(0)

        st.download_button(
            "⬇️ Download Excel",
            data=output,
            file_name="Summary_Output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error("An error occurred while processing the file.")
        st.exception(e)
