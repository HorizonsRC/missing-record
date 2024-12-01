import missing_record.generate_html
import missing_record.generate_missing_data_csvs
import missing_record.send_email
from datetime import datetime

config_file_path = "config_files/script_config.yaml"

missing_record.generate_missing_data_csvs.generate(config_file_path)
missing_record.generate_html.generate(config_file_path)
missing_record.send_email.send(
    "<p>Manual missing record report</p>"
    "<p>This can be viewed with colours at:</p>"
    r"<p>\\ares\Hydrology\Hydrology Regions\Missing Record Reporting</p>",
    "manual missing record report",
)
missing_record.send_email.copy_files(
    r"\\ares\Hydrology\Hydrology Regions\Missing Record Reporting"
    + f"\\ {datetime.today().strftime('%Y-%m-%d')}"
)
