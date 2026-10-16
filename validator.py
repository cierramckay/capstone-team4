import pandas as pd
import math
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
    required = ["item_name", "quantity", "unit"]
    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    for col in required:
        missing_values = df[col].isna()
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            missing_values |= df[col].astype("string").str.strip().eq("").fillna(False)
        if missing_values.any():
            rows = [i for i, missing in enumerate(missing_values, start=1) if missing]
            raise ValueError(f"Missing values for '{col}' in data rows: {rows}")


def validate_duplicates(df: pd.DataFrame):
    if df.duplicated(subset=["item_name"]).any():
        raise ValueError("Duplicate item names found.")


def validate_quantities(df: pd.DataFrame):
    quantities = pd.to_numeric(df["quantity"], errors="coerce")
    invalid = quantities.isna() | ~quantities.map(math.isfinite)
    if invalid.any():
        rows = [i for i, value in enumerate(invalid, start=1) if value]
        raise ValueError(f"Invalid quantity in data rows: {rows}")

    df["quantity"] = quantities
    return df


def validate_dates(df: pd.DataFrame):
    def clean_date(val):
        if pd.isna(val) or (isinstance(val, str) and not val.strip()):
            return None

        try:
            return pd.to_datetime(val).to_pydatetime()
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"Invalid date format: {val}") from exc

    dates = [clean_date(value) for value in df["expiration_date"]]
    df["expiration_date"] = pd.Series(dates, index=df.index, dtype=object)
    return df

# Main validation pipline
def validate_inventory(df: pd.DataFrame):
    df = normalize_columns(df)
    if "expiration_date" not in df.columns:
        df["expiration_date"] = None
    validate_missing_fields(df)
    validate_duplicates(df)
    df = validate_quantities(df)
    df = validate_dates(df)

    return df
