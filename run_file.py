import missing_record.generate_html, missing_record.generate_missing_data_csvs, missing_record.send_email

missing_record.generate_missing_data_csvs.generate()
missing_record.generate_html.generate()
missing_record.send_email.send()
