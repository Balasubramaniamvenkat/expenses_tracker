"""Shared account filtering for analytics endpoints."""

from typing import Optional

import pandas as pd


def filter_by_account(df: pd.DataFrame, account: Optional[str]) -> pd.DataFrame:
    if not account:
        return df

    accounts = [value.strip() for value in account.split(',') if value.strip()]
    if not accounts or any(value.casefold() == 'all accounts' for value in accounts):
        return df
    if 'Account' not in df.columns:
        return df.iloc[0:0].copy()

    return df.loc[
        df['Account'].fillna('').astype(str).str.strip().isin(accounts)
    ].copy()
