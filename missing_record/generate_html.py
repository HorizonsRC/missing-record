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

    Output
    ------
    The HTML report will be saved to the output_filepath.
    """
    # Read the CSV file and generate the HTML report
    # Return the HTML report as a pandas dataframe
    missing_records = pd.read_csv(csv_file)

    # Drop all rows that have NaN values in all columns except the first one
    missing_records = missing_records.dropna(
        subset=missing_records.columns[1:], how="all"
    )

    # Parse all columns except the first one as timedelta objects
    missing_records.iloc[:, 1:] = missing_records.iloc[:, 1:].astype("timedelta64[s]")

    # Convert all timedelta objects to total hours
    missing_records.iloc[:, 1:] = missing_records.iloc[:, 1:].map(
        lambda x: x.total_seconds() / 3600
    )

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
    styled_df = missing_records.style.map(
        style_cell_colour, subset=missing_records.columns[1:]
    )

    # Format the missing hour values to 2 decimal places unless they are NaN
    styled_df = styled_df.format(
        {
            col: lambda x: f"{x:.2f}h" if not pd.isna(x) else "-"
            for col in missing_records.columns[1:]
        }
    )

    # Remove the index column and left align the first column
    styled_df = styled_df.set_properties(**{"text-align": "left"}).hide(axis="index")

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


def generate_highlights():
    output = None
    return output


def generate():
    generate_html("./output_csv/output.csv", "./output_html/output.html")
    with open("config_files/script_config.yaml") as file:
        config = yaml.safe_load(file)
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
            generate_title(region, config["start"], config["end"]),
        )
    print("HTML reports generated successfully!")


if __name__ == "__main__":
    generate()
