"""Missing record script."""

import csv
import time
import warnings
import numpy as np
import pandas as pd
import yaml
from hydrobot.data_acquisition import get_data
from pandas.tseries.frequencies import to_offset
import missing_record.site_list_merge as site_list_merge

debug_site_list = [
    "Lake Wiritoa",
]
debug_meas_list = [
    "Water Temperature",
]


def generate(config_file_path, debug=False):
    warnings.filterwarnings("ignore", message=".*Empty hilltop response:.*")

    with open(config_file_path) as file:
        config = yaml.safe_load(file)
    sites = site_list_merge.get_sites(site_list_merge.connect_to_db())

    # This gets rid of sites that are assigned to multiple regions
    # Currently it just picks out the last region alphabetically
    # So lakes gets chosen over central, which is the only problem I have found currently
    # This might break for sites assigned to 3+ regions?
    # But it's good enough for now
    sites = sites[~sites.duplicated(keep="first", subset="SiteName")].sort_values(
        ["SiteName", "RegionName"]
    )

    # Smaller site list for debugging, won't be used in actual runs
    if debug:
        sites = sites[sites["SiteName"].isin(debug_site_list)]

    with open("config_files/Active_Measurements.csv", newline="") as f:
        reader = csv.reader(f)
        measurements = [(row[0], row[1]) for row in reader if len(row) > 0]

    # Smaller site list for debugging, won't be used in actual runs
    if debug:
        measurements = [m for m in measurements if m[1] in debug_meas_list]

    # Get the "type" (bucket) of each measurement and
    # Remove duplicates without changing order
    measurement_buckets = list(dict.fromkeys([m[1] for m in measurements]))

    # Sort sites into regions
    region_stats_dict = {
        "Northern": [],
        "Eastern": [],
        "Central": [],
        "Special": [],
    }
    regions_dict = {
        "Northern": ["NORTHERN"],
        "Eastern": ["EASTERN"],
        "Central": ["CENTRAL"],
        "Special": ["LAKES AND WQ", "Arawhata Piezometers"],
    }
    for _, site in sites.iterrows():
        for region in regions_dict:
            if site.RegionName in regions_dict[region]:
                region_stats_dict[region].append(site.SiteName)

    # manual start/end date for sites
    starting_sites_path = "//tqm/Hydrology/Reports/Report CSVs/MR_Sites_Open.csv"
    ending_sites_path = "//tqm/Hydrology/Reports/Report CSVs/MR_Sites_Closed.csv"
    site_start_frame = pd.read_csv(starting_sites_path)
    site_start_frame["Datetime"] = pd.to_datetime(
        site_start_frame["Datetime"], format="%d/%m/%Y %H:%M"
    )
    site_end_frame = pd.read_csv(ending_sites_path)
    site_end_frame["Datetime"] = pd.to_datetime(
        site_end_frame["Datetime"], format="%d/%m/%Y %H:%M"
    )

    def report_missing_record(site, measurement, start, end):
        """Reports minutes missing for a given site/measurement pair."""
        start_of_site = site_start_frame[
            (site_start_frame["Site"] == site)
            & (site_start_frame["Measurement"] == measurement[0])
            & (site_start_frame["Datetime"] < pd.to_datetime(end))
            & (site_start_frame["Datetime"] > pd.to_datetime(start))
        ]
        end_of_site = site_end_frame[
            (site_end_frame["Site"] == site)
            & (site_end_frame["Measurement"] == measurement[0])
            & (site_end_frame["Datetime"] < pd.to_datetime(end))
            & (site_end_frame["Datetime"] > pd.to_datetime(start))
        ]
        if len(start_of_site) > 1:
            raise Exception(
                f"Multiple start dates in config for site={site}, meas={measurement} between {start} and"
                f" {end}, should be max 1."
            )
        elif len(start_of_site) == 1:
            start = str(start_of_site["Datetime"].iloc[0])
        if len(end_of_site) > 1:
            raise Exception(
                f"Multiple end dates in config for site={site}, meas={measurement} between {start} and"
                f" {end}, should be max 1."
            )
        elif len(end_of_site) == 1:
            end = end_of_site["Datetime"].iloc[0]

        _, blob = get_data(
            config["base_url"],
            config["hts"],
            site,
            measurement[0],
            start,
            end,
        )

        if blob is None or len(blob) == 0:
            return (np.nan, np.nan)

        series = blob[0].data.timeseries[blob[0].data.timeseries.columns[0]]
        series.index = pd.DatetimeIndex(series.index)

        freq = "24h" if measurement[1] in ["Rainfall", "Rainfall Backup"] else "1h"
        # Another option for if frequency is consistent:
        # freq = infer_frequency(series.index, method="mode")

        # Sample data at frequency
        series.index = series.index.floor(freq)
        series = series[~series.index.duplicated(keep="first")]

        series = series.reindex(pd.date_range(start, end, freq=freq))
        missing_points = series.asfreq(freq).isna().sum()
        return (
            str(missing_points * pd.to_timedelta(to_offset(freq))),
            str(pd.Timestamp(end) - pd.Timestamp(start)),
        )

    all_stats_dict = {}
    all_sites_totals = {}
    start_timer = time.time()
    for _, site in sites.iterrows():
        site_stats_list = []
        site_totals_list = []
        for meas in measurements:
            try:
                (missing, total) = report_missing_record(
                    site["SiteName"], meas, config["start"], config["end"]
                )
                site_stats_list.append(missing)
                site_totals_list.append(total)
            except ValueError as e:
                print(
                    f"Site '{site['SiteName']}' with meas '{meas[0]}' doesn't work: {e}"
                )
                site_stats_list.append(np.nan)
                site_totals_list.append(np.nan)

        all_stats_dict[site["SiteName"]] = site_stats_list
        all_sites_totals[site["SiteName"]] = site_totals_list
        print(site.SiteName, time.time() - start_timer)

    bucket_stats_dict = {}
    bucket_totals_dict = {}
    diff = pd.to_datetime(config["end"]) - pd.to_datetime(config["start"])
    for site in all_stats_dict:
        site_bucket_dict = dict([(m, []) for m in measurement_buckets])
        site_totals_dict = dict([(m, []) for m in measurement_buckets])
        for i in zip(
            measurements, all_stats_dict[site], all_sites_totals[site], strict=True
        ):
            site_bucket_dict[i[0][1]].append(i[1])
            site_totals_dict[i[0][1]].append(i[2])
        for bucket in site_bucket_dict:
            site_totals_dict[bucket] = sum(
                [
                    pd.to_timedelta(n) if n is not np.nan else pd.to_timedelta("0")
                    for n in site_totals_dict[bucket]
                ],
                pd.to_timedelta("0"),
            )
            nanless = [m for m in site_bucket_dict[bucket] if m is not np.nan]
            if len(nanless) == 0:
                site_bucket_dict[bucket] = np.nan
            elif len(nanless) == 1:
                site_bucket_dict[bucket] = nanless[0]
            else:
                print("Multiple data sources in one bucket")
                print(site, bucket, nanless)
                # sum
                site_bucket_dict[bucket] = sum(
                    [pd.to_timedelta(n) for n in nanless], pd.to_timedelta("0")
                )
                # or max?
                # site_bucket_dict[bucket] = max([pd.to_timedelta(n) for n in nanless])

        bucket_stats_dict[site] = [site_bucket_dict[m] for m in measurement_buckets]
        bucket_totals_dict[site] = [site_totals_dict[m] for m in measurement_buckets]

    def write_dict_to_file(
        output_file, input_dict, input_totals, title_list, output_as_percent
    ):
        """Writes a dict into csv."""
        with open(output_file, "w", newline="", encoding="utf-8") as output:
            wr = csv.writer(output)
            wr.writerow(["Sites"] + title_list)
            for site in input_dict:
                if output_as_percent:
                    wr.writerow(
                        [site]
                        + [
                            (missing / total) * 100 if missing is not np.nan else np.nan
                            for (missing, total) in zip(
                                input_dict[site], input_totals[site], strict=True
                            )
                        ]
                    )
                else:
                    wr.writerow([site] + input_dict[site])
        with open(
            output_file[:-4] + "_totals" + output_file[-4:],
            "w",
            newline="",
            encoding="utf-8",
        ) as output:
            wr = csv.writer(output)
            wr.writerow(["Sites"] + title_list)
            for site in input_totals:
                wr.writerow([site] + input_totals[site])

    write_dict_to_file(
        "output_csv/output.csv",
        bucket_stats_dict,
        bucket_totals_dict,
        measurement_buckets,
        False,
    )
    write_dict_to_file(
        "output_csv/output_percent.csv",
        bucket_stats_dict,
        bucket_totals_dict,
        measurement_buckets,
        True,
    )
    for region in regions_dict:
        write_dict_to_file(
            f"output_csv/output_{region}.csv",
            {
                k: bucket_stats_dict[k]
                for k in bucket_stats_dict
                if k in region_stats_dict[region]
            },
            {
                k: bucket_totals_dict[k]
                for k in bucket_stats_dict
                if k in region_stats_dict[region]
            },
            measurement_buckets,
            False,
        )

    # Annex splitting
    def filter_list(unfiltered, filter):
        return [p[0] for p in zip(unfiltered, filter) if p[1]]

    annex_1_filter = [
        True if m in config["Annex_1_buckets"] else False for m in measurement_buckets
    ]
    annex_2_filter = [
        True if m in config["Annex_2_buckets"] else False for m in measurement_buckets
    ]
    annex_3_dict = {
        k: bucket_stats_dict[k]
        for k in config["Annex_3_sites"]
        if k in bucket_stats_dict
    }
    annex_3_totals = {
        k: bucket_totals_dict[k]
        for k in config["Annex_3_sites"]
        if k in bucket_totals_dict
    }

    rivers_dict = {
        k: bucket_stats_dict[k]
        for k in bucket_stats_dict
        if k not in config["Annex_3_sites"]
    }
    rivers_totals = {
        k: bucket_totals_dict[k]
        for k in bucket_totals_dict
        if k not in config["Annex_3_sites"]
    }
    annex_1_dict = {k: filter_list(rivers_dict[k], annex_1_filter) for k in rivers_dict}
    annex_2_dict = {k: filter_list(rivers_dict[k], annex_2_filter) for k in rivers_dict}
    annex_1_totals = {
        k: filter_list(rivers_totals[k], annex_1_filter) for k in rivers_totals
    }
    annex_2_totals = {
        k: filter_list(rivers_totals[k], annex_2_filter) for k in rivers_totals
    }

    write_dict_to_file(
        "output_csv/output_annex1.csv",
        annex_1_dict,
        annex_1_totals,
        filter_list(measurement_buckets, annex_1_filter),
        False,
    )
    write_dict_to_file(
        "output_csv/output_annex2.csv",
        annex_2_dict,
        annex_2_totals,
        filter_list(measurement_buckets, annex_2_filter),
        False,
    )
    write_dict_to_file(
        "output_csv/output_annex3.csv",
        annex_3_dict,
        annex_3_totals,
        measurement_buckets,
        False,
    )
    """    write_dict_to_file(
        "output_csv/output_totals.csv", bucket_totals_dict, measurement_buckets, False
    )"""

    # totals
    rivers_totals = {
        k: bucket_totals_dict[k]
        for k in bucket_totals_dict
        if k not in config["Annex_3_sites"]
    }
    annex_1_totals = {
        k: filter_list(rivers_totals[k], annex_1_filter) for k in rivers_totals
    }
    annex_2_totals = {
        k: filter_list(rivers_totals[k], annex_2_filter) for k in rivers_totals
    }
    annex_3_totals = {
        k: bucket_totals_dict[k]
        for k in config["Annex_3_sites"]
        if k in bucket_stats_dict
    }

    totals_dict = {
        k: pd.to_timedelta(0)
        for k in [
            "total_1_numerator",
            "total_2_numerator",
            "total_3_numerator",
            "total_1_denominator",
            "total_2_denominator",
            "total_3_denominator",
        ]
    }

    for pair in [
        ["total_1_numerator", annex_1_dict],
        ["total_2_numerator", annex_2_dict],
        ["total_3_numerator", annex_3_dict],
        ["total_1_denominator", annex_1_totals],
        ["total_2_denominator", annex_2_totals],
        ["total_3_denominator", annex_3_totals],
    ]:
        for site in pair[1]:
            for i in [pd.to_timedelta(a) for a in pair[1][site] if a is not np.nan]:
                totals_dict[pair[0]] += i

    with open("output_csv/totals.csv", "w", newline="", encoding="utf-8") as output:
        wr = csv.writer(output)
        wr.writerow(["\\", "annex_1", "annex_2", "annex_3"])
        wr.writerow(
            [
                "Total",
                totals_dict["total_1_numerator"],
                totals_dict["total_2_numerator"],
                totals_dict["total_3_numerator"],
            ]
        )
        wr.writerow(
            [
                "Percentage",
                (
                    totals_dict["total_1_numerator"]
                    / totals_dict["total_1_denominator"]
                    * 100
                    if totals_dict["total_1_denominator"] > pd.to_timedelta(0)
                    else "None"
                ),
                (
                    totals_dict["total_2_numerator"]
                    / totals_dict["total_2_denominator"]
                    * 100
                    if totals_dict["total_2_denominator"] > pd.to_timedelta(0)
                    else "None"
                ),
                (
                    totals_dict["total_3_numerator"]
                    / totals_dict["total_3_denominator"]
                    * 100
                    if totals_dict["total_3_denominator"] > pd.to_timedelta(0)
                    else "None"
                ),
            ]
        )
        wr.writerow(
            [
                "Length of record",
                totals_dict["total_1_denominator"],
                totals_dict["total_2_denominator"],
                totals_dict["total_3_denominator"],
            ]
        )


if __name__ == "__main__":
    generate("config_files/script_config.yaml", debug=False)
