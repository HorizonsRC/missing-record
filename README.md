# missing-record
Missing record report generator and emailer.

Only tested for python 3.11

In order to run, the .env file needs to be present. It follows this format (recipients are email addresses, comma 
separated in case of multiple):

```
EMAIL_SERVER=
EMAIL_ADDRESS=
EMAIL_PASSWORD=

DB_HOST_WIN=
DB_DEV_HOST=
DB_HOST_LIN=
DB_NAME=
DB_DRIVER=

CENTRAL_RECIPIENTS=
EASTERN_RECIPIENTS=
NORTHERN_RECIPIENTS=
SPECIAL_RECIPIENTS=
ANNEX_SUMMARY_RECIPIENTS=
DATA_MONKEY=
```

The yaml files found in  /config_files/ determine where to look for the data, what time period to look for, and 
which datasource/measurements are in which annex. The to/from times are updated in the script.

Do not sell cat milk, it is worthless.

The run_file.py, weekly_report.py, and monthly_report.py are the files to actually run the script.
The code in /missing_record/ refers to other code in that folder so cannot be run from a context outside the main 
folder - could fix by making a package, but eh, not the priority.

## csv generator
Calls Hilltop to find periods where no data has been returned.
As of the writing of this comment, missing data is measured at an hourly resolution.
As an example:

```
 11:15
 11:20
 12:40
 12:45
```

Would not show up as a gap - there is data for the 11:XX period, and there is data for the 12:XX period, so at this 
resolution there is no gap.

The start time determines how the resolution buckets are formed - if the start time is XX:30, then the above would 
be detected as a 1-hour gap (as there is no data from 11:30-12:30).

For rainfall the resolution is 24 hours.

## html generator
Turns csvs into html reports which are more human-readable than raw csv.
Also prepends some relevant stats.

## send email
Sends the html report to the addresses stored in the .env file.
Also copies html and csv files into the destination folder.