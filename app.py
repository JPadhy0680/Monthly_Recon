# Sort data first
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
                from_date = current_date - pd.Timedelta(days=3)  # Friday
                to_date = current_date - pd.Timedelta(days=1)    # Sunday
            else:
                from_date = current_date - pd.Timedelta(days=1)
                to_date = current_date - pd.Timedelta(days=1)
        else:
            # Subsequent records
            prev_download_date = group.loc[i - 1, 'Download Date']
            from_date = prev_download_date
            to_date = current_date - pd.Timedelta(days=1)

        # Filter data within this date range
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

# Format dates
summary['Downloaded Date'] = summary['Downloaded Date'].dt.strftime('%d-%b-%y')
summary['From'] = summary['From'].dt.strftime('%d-%b-%y')
summary['To'] = summary['To'].dt.strftime('%d-%b-%y')
