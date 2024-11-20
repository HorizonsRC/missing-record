"""Script for merging site list from SQL query with that from Hilltop Server."""

import platform
import os
from dotenv import load_dotenv

import pandas as pd
import sqlalchemy as db
from sqlalchemy.engine import URL

# Load the environment variables
load_dotenv()

# Get the database details
DB_HOST_WIN = os.getenv("DB_HOST_WIN")
DB_HOST_LIN = os.getenv("DB_HOST_LIN")
DB_NAME = os.getenv("DB_NAME")
DB_DRIVER = os.getenv("DB_DRIVER")
DB_DEV_HOST = os.getenv("DB_DEV_HOST")


def connect_to_db():
    """Connect to the Hilltop database.
    Returns
    -------
    sqlalchemy.engine.base.Connection
        A connection to the Hilltop database.
    """
    if platform.system() == "Windows":
        hostname = DB_HOST_WIN
    elif platform.system() == "Linux":
        hostname = DB_HOST_LIN
    else:
        raise OSError("What is this, a mac? We don't do that here.")
    connection_url = URL.create(
        "mssql+pyodbc",
        host=hostname,
        database=DB_NAME,
        query={"driver": DB_DRIVER},
    )
    engine = db.create_engine(connection_url)
    return engine


def connect_to_dev_db():
    """Connect to the Hilltop database.
    Returns
    -------
    sqlalchemy.engine.base.Engine
        A connection to the Hilltop database.
    """
    if platform.system() == "Windows":
        hostname = DB_DEV_HOST
    else:
        raise OSError("What is this, a mac? We don't do that here.")
    connection_url = URL.create(
        "mssql+pyodbc",
        host=hostname,
        database="Piri",
        query={"driver": DB_DRIVER},
    )
    engine = db.create_engine(connection_url)
    return engine


def get_sites(engine):
    """
    Gives sites to check for missing data.

    Returns
    -------
    pd.Dataframe
        All relevant sites + id + region
    """
    with open("sql_queries/get_sites.sql") as f:
        query = f.read()
        return pd.read_sql(query, engine)


def get_measurements(engine):
    """
    Gives measurements to check for missing data.

    Returns
    -------
    pd.Dataframe
        All measurements with data sources
    """
    with open("sql_queries/get_measurements.sql") as f:
        query = f.read()
        measurement_list = pd.read_sql(query, engine)
    measurement_list["MeasurementFullName"] = (
        measurement_list["MeasurementName"]
        + " ["
        + measurement_list["DataSourceName"]
        + "]"
    )
    return measurement_list


def insert_missing_totals(missing_dict, engine):
    with open("sql_queries/insert_missing.sql") as f:
        query = f.read()
    with engine.begin() as conn:
        conn.execute(db.text(query), missing_dict)


def insert_recorded_totals(totals_dict, engine):
    with open("sql_queries/insert_total.sql") as f:
        query = f.read()
    with engine.begin() as conn:
        conn.execute(db.text(query), totals_dict)
