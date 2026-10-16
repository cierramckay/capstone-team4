import pandas as pd
import re
from datetime import datetime
from schema import UNIFIED_COLUMNS

# Column normalization
def normalize_columns(df: pd.DataFrame):
    new_cols = {}

    for col in df.columns:
        col_lower = str(col).strip().lower()
        if col_lower in UNIFIED_COLUMNS:
            new_cols[col] = UNIFIED_COLUMNS[col_lower]
        else:
            new_cols[col] = col_lower  # fallback

    df = df.rename(columns=new_cols)
    return df


# Validation helpers
def validate_missing_fields(df: pd.DataFrame):
    required = ["item_name", "quantity", "unit", "expiration_date"]
    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required fields: {missing}")


def validate_duplicates(df: pd.DataFrame):
    if df.duplicated(subset=["item_name"]).any():
        raise ValueError("Duplicate item names found.")


def validate_dates(df: pd.DataFrame):
    def clean_date(val):
        try:
            return pd.to_datetime(val)
        except:
            raise ValueError(f"Invalid date format: {val}")

    df["expiration_date"] = df["expiration_date"].apply(clean_date)
    return df

# Main validation pipline
def validate_inventory(df: pd.DataFrame):
    df = normalize_columns(df)
    validate_missing_fields(df)
    validate_duplicates(df)
    df = validate_dates(df)

    return df
