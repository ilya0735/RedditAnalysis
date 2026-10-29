from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
from pydantic import ValidationError

from .validation_schema import RedditCommentSchema


class Validator:
    def __init__(self, batch_size: int = 10000):
        self.batch_size = batch_size

    def run(
        self,
        raw_file_path: str | Path,
        corrupted_file_path: str | Path,
        mode: str | None = "save_corrupted",
    ) -> pd.DataFrame:

        parquet_file = pq.ParquetFile(raw_file_path)
        clear_chunks: list[pd.DataFrame] = []
        corrupted_chunks: list[pd.DataFrame] = []
        valid_count = 0
        invalid_count = 0

        for batch in parquet_file.iter_batches(batch_size=self.batch_size):
            chunk = batch.to_pandas()
            clear_data_chunk = []
            corrupted_data_chunk = []

            for row in chunk.to_dict(orient="records"):
                try:
                    validated = RedditCommentSchema.model_validate(row)
                    valid_count += 1
                    clear_data_chunk.append(validated.model_dump())
                except ValidationError:
                    invalid_count += 1
                    if mode == "save_corrupted":
                        corrupted_data_chunk.append(row)

            if clear_data_chunk:
                clear_chunks.append(pd.DataFrame(clear_data_chunk))
            if corrupted_data_chunk:
                corrupted_chunks.append(pd.DataFrame(corrupted_data_chunk))

        if mode == "save_corrupted" and corrupted_chunks and corrupted_file_path:
            df_corrupted = pd.concat(corrupted_chunks, ignore_index=True)
            df_corrupted.to_json(
                corrupted_file_path,
                orient="records",
                lines=True,
                force_ascii=False,
            )

        print(f"[{Path(raw_file_path).name}] Валидных: {valid_count} | Битых: {invalid_count}")

        return (
            pd.concat(clear_chunks, ignore_index=True)
            if clear_chunks
            else pd.DataFrame()
        )