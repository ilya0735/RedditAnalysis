import numpy as np
import pandas as pd


class Transformer:
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df.copy()

        df = df.copy()

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
        df["thread_avg_score"] = (df.groupby("link_id")["score"].transform("mean").round(2))

        return df