from typing import Any

import pandas as pd
import pyarrow.parquet as pq
from pydantic import ValidationError
from .validation_schema import RedditCommentSchema


class Validator:
    def __init__(self, raw_file_path: str, corrupted_file_path: str):
        self.raw_file_path = raw_file_path
        self.corrupted_file_path = corrupted_file_path
        self.clear_chunks: list[pd.DataFrame] = []
        self.corrupted_chunks: list[pd.DataFrame] = []
        self.valid_count = 0
        self.invalid_count = 0

    def _validate_logic(self) -> None:
        parquet_file = pq.ParquetFile(self.raw_file_path)

        for batch in parquet_file.iter_batches(batch_size=10000):
            chunk = batch.to_pandas()
            clear_data_chunk = []
            corrupted_data_chunk = []

            for row in chunk.to_dict(orient="records"):
                try:
                    validated = RedditCommentSchema.model_validate(row)
                    self.valid_count += 1
                    clear_data_chunk.append(validated.model_dump())
                except ValidationError:
                    self.invalid_count += 1
                    corrupted_data_chunk.append(row)

            if clear_data_chunk:
                self.clear_chunks.append(pd.DataFrame(clear_data_chunk))
            if corrupted_data_chunk:
                self.corrupted_chunks.append(pd.DataFrame(corrupted_data_chunk))

    def run(self, mode: Any = "save_corrupted") -> pd.DataFrame:
        self.clear_chunks.clear()
        self.corrupted_chunks.clear()
        self.valid_count = 0
        self.invalid_count = 0

        self._validate_logic()

        df_clear = (
            pd.concat(self.clear_chunks, ignore_index=True)
            if self.clear_chunks
            else pd.DataFrame()
        )

        if mode == "save_corrupted" and self.corrupted_chunks:
            df_corrupted = pd.concat(self.corrupted_chunks, ignore_index=True)
            df_corrupted.to_json(
                self.corrupted_file_path,
                orient="records",
                lines=True,
                force_ascii=False,
            )

        return df_clear