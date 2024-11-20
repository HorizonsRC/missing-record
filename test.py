import missing_record.generate_missing_data_csvs as gcsv
import missing_record.generate_html as ghtml

gcsv.generate("config_files/script_config.yaml", debug=False)
ghtml.generate("config_files/script_config.yaml")
