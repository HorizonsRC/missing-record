"""Tools for displaying the missing record report in HTML format."""

import pandas as pd
import numpy as np
import yaml
from matplotlib import colors

from missing_record.utils import get_hex_colour, invert_colour


def generate_html(
    csv_file, output_filepath, title_info="", bad_hours=744, cmap="autumn_r"
):
    """Generate an HTML report of the missing records in the CSV file.

    Parameters
    ----------
    csv_file : str
        The path to the CSV file containing the missing records.
    output_filepath : str
        The path to save the generated HTML report.
    title_info : str, optional
        Any title information that should go above the html table.
    bad_hours : int, optional
        The number of hours that should be considered a very bad record.
        Default is 744 hours (31 days).
        This is only a visual indicator and does not affect the data - it specifies the
        number of hours that should be the most extreme colour on the colourmap.
    cmap : str, optional
        The name of the matplotlib colourmap to use for the background colour of the
        cells. Default is 'autumn_r'.

    Returns
    ------
    None
        The HTML report will be saved to the output_filepath.
    """
    # Read the CSV file and generate the HTML report
    # Return the HTML report as a pandas dataframe
    missing_records = pd.read_csv(csv_file)

    # Drop all rows that have NaN values in all columns except the first one
    missing_records = missing_records.dropna(
        subset=missing_records.columns[1:], how="all"
    )

    if not missing_records.empty:
        missing_records = missing_records.set_index("Sites")
        # Parse all columns except the first one as timedelta objects
        missing_records = missing_records.astype("timedelta64[s]")

        # Convert all timedelta objects to total hours
        missing_records = missing_records.map(lambda x: x.total_seconds() / 3600)
        missing_records.loc["TOTAL"] = missing_records.fillna(0).sum(axis=0)

        normfunc = colors.Normalize(vmin=0, vmax=bad_hours)

        def style_cell_colour(val):
            """Return a pandas cell_color spec."""
            hex_colour = get_hex_colour(normfunc(val), cmap=cmap)
            return f"background-color: {hex_colour};"

        def style_font_colour(val):
            """Return a pandas font_color spec."""
            inv_hex_colour = invert_colour(
                get_hex_colour(normfunc(val), cmap=cmap), hsv=True
            )
            return f"color: {inv_hex_colour};"

        # Style the cell background colour of the dataframe by passing the style function
        missing_records.index.name = None
        styled_df = missing_records.style.map(
            style_cell_colour, subset=missing_records.columns
        )

        # Format the missing hour values to 2 decimal places unless they are NaN
        styled_df = styled_df.format(
            {
                col: lambda x: f"{x:.2f}h" if not pd.isna(x) else "-"
                for col in missing_records.columns
            }
        )

        # Remove the index column and left align the first column
        styled_df = styled_df.set_properties(**{"text-align": "left"})

        # Some more detailed styling
        styled_df.set_table_styles(
            [
                # Left align all the table headers
                {"selector": "th, thead", "props": [("text-align", "left")]},
                # Set all fonts to a gorgeous monospace font
                {"selector": "td, th", "props": [("font-family", "monospace")]},
                # Add a thin lightgrey border around the cells
                {"selector": ", td, th", "props": [("border", "1px solid #d3d3d3")]},
                # Collapse the cell borders into single lines
                {"selector": "", "props": [("border-collapse", "collapse")]},
            ]
        )

        # Trying again to collapse the borders (still only successful sometimes)
        styled_df.set_properties(**{"border-collapse": "collapse"})

        html_report = styled_df.to_html(
            escape=False,
            classes=(
                "table table-striped table-bordered table-hover table-sm border-collapse"
            ),
            table_id="missing-records-table",
            justify="left",
        )

        # Output the html report to a file
        with open(output_filepath, "w") as output_file:
            output_file.write(title_info)
            output_file.write(html_report)


def generate_title(location, start_date, end_date):
    title = ""
    title += f"<h1>Monthly missing data report for {location}</h1>"
    title += f"<h3>From {start_date} to {end_date}</h3>"
    return title


def generate_highlights(csv_input: str, csv_totals: str):
    """
    Select important parts from the report.

    Parameters
    ----------
    csv_input : str
        path to input csv file
    csv_totals : str
        path to totals csv file
    Returns
    -------
    str
        html with highlights for the report
    """
    output = ""

    data = pd.read_csv(csv_input).set_index("Sites")
    totals = pd.read_csv(csv_totals).set_index("Sites")
    if not data.empty:

        percentages_total = pd.DataFrame()
        for column in data.columns:
            percentages_total[column] = pd.to_timedelta(data[column]) / pd.to_timedelta(
                totals[column]
            )
        missing_time = data.apply(pd.to_timedelta).sum(axis=1)
        length_of_record = totals.apply(pd.to_timedelta).sum(axis=1)

        output += (
            f"<p>Total missing time: {missing_time.sum()} (out of {length_of_record.sum()})</p>"
            f"Missing Percentage: {missing_time.sum() / length_of_record.sum() * 100.:.2f}%</p>"
        )
        output += (
            f"<p>Site with most missing data: {missing_time.idxmax()}, with {missing_time[missing_time.idxmax()]} "
            f"missing ({missing_time[missing_time.idxmax()] / length_of_record[missing_time.idxmax()] * 100.:.2f}%).</p>"
        )
        missing_time = missing_time.drop(missing_time.idxmax())
        if (not missing_time.empty) and length_of_record[
            missing_time.idxmax()
        ] > pd.Timedelta(0):
            output += (
                f"<p>Site with second most missing data: {missing_time.idxmax()}, with "
                f"{missing_time[missing_time.idxmax()]} missing "
                f"({missing_time[missing_time.idxmax()] / length_of_record[missing_time.idxmax()] * 100.:.2f}%).</p>"
            )
            missing_time = missing_time.drop(missing_time.idxmax())
            if (not missing_time.empty) and length_of_record[
                missing_time.idxmax()
            ] > pd.Timedelta(0):
                output += (
                    f"<p>Site with third most missing data: {missing_time.idxmax()}, with "
                    f"{missing_time[missing_time.idxmax()]} missing "
                    f"({missing_time[missing_time.idxmax()] / length_of_record[missing_time.idxmax()] * 100.:.2f}%).</p>"
                )

    return output


def generate(file_path):
    with open(file_path) as file:
        config = yaml.safe_load(file)
    generate_html(
        "./output_csv/output.csv",
        "./output_html/output.html",
        title_info=generate_title("all regions", config["start"], config["end"])
        + generate_highlights(
            f"./output_csv/output.csv",
            f"./output_csv/output_totals.csv",
        ),
    )
    for region in [
        "Central",
        "Eastern",
        "Northern",
        "Special",
        "annex1",
        "annex2",
        "annex3",
    ]:
        generate_html(
            f"./output_csv/output_{region}.csv",
            f"./output_html/output_{region}.html",
            title_info=generate_title(region, config["start"], config["end"])
            + generate_highlights(
                f"./output_csv/output_" f"{region}.csv",
                f"./output_csv/output_" f"{region}_totals.csv",
            ),
        )
    print("HTML reports generated successfully!")


if __name__ == "__main__":
    generate("config_files/script_config.yaml")
