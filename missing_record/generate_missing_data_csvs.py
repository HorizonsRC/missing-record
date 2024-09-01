"""Missing record script."""

import csv
import time
import warnings

import numpy as np
import pandas as pd
import yaml
from hydrobot.data_acquisition import get_data
from hydrobot.utils import infer_frequency
from pandas.tseries.frequencies import to_offset

import missing_record.site_list_merge as site_list_merge


def generate():
    warnings.filterwarnings("ignore", message=".*Empty hilltop response:.*")

    with open("config_files/script_config.yaml") as file:
        config = yaml.safe_load(file)

    sites = site_list_merge.get_sites(site_list_merge.connect_to_db())

    with open("config_files/Active_Measurements.csv", newline="") as f:
        reader = csv.reader(f)
        measurements = [(row[0], row[1]) for row in reader if len(row) > 0]

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
    annex_3_sites = {}
    for _, site in sites.iterrows():
        for region in regions_dict:
            if site.RegionName in regions_dict[region]:
                region_stats_dict[region].append(site.SiteName)

    def report_missing_record(site, measurement, start, end):
        """Reports minutes missing."""
        _, blob = get_data(
            config["base_url"],
            config["hts"],
            site,
            measurement,
            start,
            end,
        )

        if blob is None or len(blob) == 0:
            return np.nan

        series = blob[0].data.timeseries[blob[0].data.timeseries.columns[0]]
        series.index = pd.DatetimeIndex(series.index)

        freq = infer_frequency(series.index, method="mode")
        series = series.reindex(pd.date_range(start, end, freq=freq))
        missing_points = series.asfreq(freq).isna().sum()
        return str(missing_points * pd.to_timedelta(to_offset(freq)))

    all_stats_dict = {}
    start_timer = time.time()
    for _, site in sites.iterrows():
        site_stats_list = []
        for meas in measurements:
            try:
                site_stats_list.append(
                    report_missing_record(
                        site["SiteName"], meas[0], config["start"], config["end"]
                    )
                )
            except ValueError as e:
                print(
                    f"Site '{site['SiteName']}' with meas '{meas[0]}' doesn't work: {e}"
                )
                site_stats_list.append(np.nan)

        all_stats_dict[site["SiteName"]] = site_stats_list
        print(site.SiteName, time.time() - start_timer)

    # convert to measurement bucket
    measurement_buckets = list(set([m[1] for m in measurements]))

    bucket_stats_dict = {}
    bucket_totals_dict = {}
    diff = pd.to_datetime(config["end"]) - pd.to_datetime(config["start"])
    for site in all_stats_dict:
        site_bucket_dict = dict([(m, []) for m in measurement_buckets])
        site_totals_dict = dict([(m, []) for m in measurement_buckets])
        for i in zip(measurements, all_stats_dict[site], strict=True):
            site_bucket_dict[i[0][1]].append(i[1])
        for bucket in site_bucket_dict:
            nanless = [m for m in site_bucket_dict[bucket] if m is not np.nan]
            site_totals_dict[bucket] = diff * len(nanless)
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

    def write_dict_to_file(output_file, input_dict, title_list, output_as_percent):
        """Writes a dict into csv."""
        diff = pd.to_datetime(config["end"]) - pd.to_datetime(config["start"])
        with open(output_file, "w", newline="", encoding="utf-8") as output:
            wr = csv.writer(output)
            wr.writerow(["Sites"] + title_list)
            for site in input_dict:
                if output_as_percent:
                    wr.writerow(
                        [site]
                        + [
                            (i / diff) * 100 if i is not np.NaN else np.NaN
                            for i in input_dict[site]
                        ]
                    )
                else:
                    wr.writerow([site] + input_dict[site])

    write_dict_to_file(
        "output_csv/output.csv", bucket_stats_dict, measurement_buckets, False
    )
    write_dict_to_file(
        "output_csv/output_percent.csv", bucket_stats_dict, measurement_buckets, True
    )
    for region in regions_dict:
        write_dict_to_file(
            f"output_csv/output_{region}.csv",
            {
                k: bucket_stats_dict[k]
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

    rivers_dict = {
        k: bucket_stats_dict[k]
        for k in bucket_stats_dict
        if k not in config["Annex_3_sites"]
    }
    annex_1_dict = {k: filter_list(rivers_dict[k], annex_1_filter) for k in rivers_dict}
    annex_2_dict = {k: filter_list(rivers_dict[k], annex_2_filter) for k in rivers_dict}

    write_dict_to_file(
        "output_csv/output_annex1.csv",
        annex_1_dict,
        filter_list(measurement_buckets, annex_1_filter),
        False,
    )
    write_dict_to_file(
        "output_csv/output_annex2.csv",
        annex_2_dict,
        filter_list(measurement_buckets, annex_2_filter),
        False,
    )
    write_dict_to_file(
        "output_csv/output_annex3.csv", annex_3_dict, measurement_buckets, False
    )
    write_dict_to_file(
        "output_csv/output_totals.csv", bucket_totals_dict, measurement_buckets, False
    )


if __name__ == "__main__":
    generate()
