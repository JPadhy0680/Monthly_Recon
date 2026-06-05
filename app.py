df = df.sort_values(by=['Source', 'Download Date'])

summary_data = []

for source, group in df.groupby('Source'):

    group = group.sort_values(by='Download Date')

    # ✅ Unique Download Dates
    unique_dates = group['Download Date'].drop_duplicates().sort_values().reset_index(drop=True)

    for i in range(len(unique_dates)):
        current_date = unique_dates[i]

        # ✅ From-To logic (same as before)
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

        # ✅ ✅ NEW FIX: COUNT ONLY BY DOWNLOAD DATE
        subset = group[group['Download Date'] == current_date]

        summary_data.append({
            'Downloaded Date': current_date,
            'Source': source,
            'From': from_date,
            'To': to_date,
            'Total Number': len(subset),  # ✅ count all rows
            'Valid': (subset['Validity'] == 'Valid').sum(),
            'Non-Valid': (subset['Validity'] == 'Non-Valid').sum()
        })

summary = pd.DataFrame(summary_data)
