import missing_record.generate_html
import missing_record.generate_missing_data_csvs
import missing_record.send_email

missing_record.generate_missing_data_csvs.generate()
missing_record.generate_html.generate()
missing_record.send_email.send()
missing_record.send_email.copy_files(
    r"\\ares\Hydrology\Hydrology Regions\Missing Record Reporting"
)
