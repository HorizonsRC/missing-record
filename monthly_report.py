import ruamel.yaml
from datetime import datetime, timedelta
import dateutil.relativedelta
import missing_record.generate_html
import missing_record.generate_missing_data_csvs
import missing_record.send_email
import os

# Rewrite config file dates
config_file_path = "config_files/monthly_config.yaml"
yaml = ruamel.yaml.YAML()
with open(config_file_path) as fp:
    data = yaml.load(fp)
data["start"] = (
    datetime.today() + dateutil.relativedelta.relativedelta(months=-1)
).strftime("%Y-%m-%d") + " 00:00"
data["end"] = datetime.today().strftime("%Y-%m-%d") + " 00:00"

with open(config_file_path, "w") as fp:
    yaml.dump(data, fp)

# Make and send reports
# missing_record.generate_missing_data_csvs.generate(config_file_path)
missing_record.generate_html.generate(config_file_path)
# missing_record.send_email.send()
destination_folder = (
    r"\\ares\Hydrology\Hydrology Regions\Missing Record Reporting\monthly_reports"
    + f"\\{datetime.today().strftime('%Y-%m-%d')}"
)
os.makedirs(destination_folder, exist_ok=True)
missing_record.send_email.copy_files(destination_folder)
