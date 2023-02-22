import unicodedata as ud

import pandas as pd


def default_player_value():
    return {"points": 0, "XP": 0}


def get_clean_columns(df: pd.DataFrame):
    return [str.strip(x) for x in df.columns]


def normalise_string(s):
    return "".join(c for c in ud.normalize("NFD", s) if ud.category(c) != "Mn")
