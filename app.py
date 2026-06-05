import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="MHRA Summary Generator", layout="wide")

st.title("📊 Data Summary Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:

    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # ✅ Clean columns
    df.columns = df.columns.str.strip()

    required_cols = ['Download Date', 'Source', 'MHRA ID', 'Validity']
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Missing columns: {missing}")
        st.stop()

    # ✅ Convert date
    df['Download Date'] = pd.to_datetime(df['Download Date'], errors='coerce')
    df = df.dropna(subset=['Download Date'])

    df = df.sort_values(by=['Source', 'Download Date'])

    summary_data = []

    for source, group in df.groupby('Source'):

        group = group.sort_values(by='Download Date')

        unique_dates = (
            group['Download Date']
            .drop_duplicates()
            .sort_values()
            .reset_index(drop=True)
        )

        for i in range(len(unique_dates)):
            current_date = unique_dates[i]

            # ✅ SOURCE-BASED DATE LOGIC

            if source.upper() == "MHRA":

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

            elif source.upper() == "ADIS":

                # ✅ Find previous Monday
                weekday = current_date.weekday()  # Monday = 0
                from_date = current_date - pd.Timedelta(days=weekday)
                to_date = current_date

            else:
                # ✅ Other sources → blank
                from_date = None
                to_date = None

            # ✅ COUNTING LOGIC (per your requirement)
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

    summary = pd.DataFrame(summary_data)

    # ✅ Format dates safely
    for col in ['Downloaded Date', 'From', 'To']:
        summary[col] = pd.to_datetime(summary[col], errors='coerce').dt.strftime('%d-%b-%y')

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
        file_name="Summary_Output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
