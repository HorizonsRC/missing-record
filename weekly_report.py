import ruamel.yaml
from datetime import datetime, timedelta
import missing_record.generate_html
import missing_record.generate_missing_data_csvs
import missing_record.send_email
import os

# Rewrite config file dates
config_file_path = "config_files/weekly_config.yaml"
yaml = ruamel.yaml.YAML()
with open(config_file_path) as fp:
    data = yaml.load(fp)
finish_date = datetime.today()
data["start"] = (finish_date - timedelta(days=7)).strftime("%Y-%m-%d") + " 00:00:00"
data["end"] = (finish_date - timedelta(days=1)).strftime("%Y-%m-%d") + " 23:59:59"

with open(config_file_path, "w") as fp:
    yaml.dump(data, fp)

# Make and send reports
missing_record.generate_missing_data_csvs.generate(config_file_path)
missing_record.generate_html.generate(config_file_path)

destination_folder = (
    r"\\ares\Hydrology\Hydrology Regions\Missing Record Reporting\weekly_reports"
    + f"\\{finish_date.strftime('%Y-%m-%d')}"
)
os.makedirs(destination_folder, exist_ok=True)
missing_record.send_email.copy_files(destination_folder)

missing_record.send_email.send(
    "<p>Weekly missing record report</p>"
    "<p>This can be viewed with colours at:</p>"
    r"<p>\\ares\Hydrology\Hydrology Regions\Missing Record Reporting\weekly_reports</p>",
    "weekly missing record report",
)
