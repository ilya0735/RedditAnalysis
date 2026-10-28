from pathlib import Path

import numpy as np
import pandas as pd

from src.config import CORRUPTED_DATA_PATH, CLEANED_DATA_PATH, RAW_DATA_PATH
from validation import Validator


CORRUPTED_DATA_PATH.mkdir(parents=True, exist_ok=True)
CLEANED_DATA_PATH.mkdir(parents=True, exist_ok=True)


raw_files = list(Path(RAW_DATA_PATH).glob("*.parquet"))
row_file_path = raw_files[2]
corrupted_file_path = CORRUPTED_DATA_PATH / 'programming.jsonl'

if not row_file_path.exists():
    print(f"Файл {row_file_path.name} не найден.")
    raise FileNotFoundError


validator = Validator(row_file_path, corrupted_file_path)
pure_dataframe = validator.run()


class Transformer:
    def __init__(self, row_file_path, corrupted_file_path):
        self.row_file_path = row_file_path
        self.corrupted_file_path = corrupted_file_path
        self.validator = Validator(row_file_path, corrupted_file_path)
        self.df = validator.run()

    def _transform(self, df):
        self.df = self.df()

        df["created_utc"] = pd.to_datetime(
            pd.to_numeric(df["created_utc"], errors="coerce"), unit="s"
        )

        df["hour"] = df["created_utc"].dt.hour
        df["day_of_week"] = df["created_utc"].dt.dayofweek
        df["month"] = df["created_utc"].dt.month
        df["year"] = df["created_utc"].dt.year

        df["body_length"] = df["body"].fillna("").str.len()

        df["length_category"] = pd.cut(
            df["body_length"],
            bins=[-1, 99, 500, np.inf],
            labels=["короткие", "средние", "длинные"],
        ).astype(str)

        df["archived"] = (
            df["archived"].fillna("false").str.lower().isin(["true", "1"])
        )
        df["deleted"] = (df["author"] == "[deleted]") | (
            df["body"].isin(["[deleted]", "[removed]"])
        )
        df["edited"] = (
            ~df["edited"]
            .fillna("false")
            .str.lower()
            .isin(["false", "0", "none", ""])
        )

        df["thread_comment_count"] = df.groupby("link_id")["id"].transform("count")
        df["thread_avg_score"] = (
            df.groupby("link_id")["score"].transform("mean").round(2)
        )

        return df

    def get_df(self):
        self.df = self._transform(self.df)
        return self.df