import pandas as pd
import pyarrow.parquet as pq
from pydantic import ValidationError

from validation_schema import RedditCommentSchema


class Validator:
    def __init__(self, row_file_path, corrupted_file_path):
        self.row_file_path = row_file_path
        self.corrupted_file_path = corrupted_file_path
        self.clear_chunks = []
        self.corrupted_chunks = []
        self.valid_count = 0
        self.invalid_count = 0
        self.parquet_file = pq.ParquetFile(row_file_path)

    def _validate_logic(self):
        for batch in self.parquet_file.iter_batches(batch_size=10000):
            chunk = batch.to_pandas()

            clear_data_chunk = []
            corrupted_data_chunk = []

            for row in chunk.to_dict(orient="records"):
                try:
                    RedditCommentSchema.model_validate(row)
                    self.valid_count += 1
                    clear_data_chunk.append(row)
                except ValidationError:
                    self.invalid_count += 1
                    corrupted_data_chunk.append(row)

            if clear_data_chunk:
                self.clear_chunks.append(pd.DataFrame(clear_data_chunk))
            if corrupted_data_chunk:
                self.corrupted_chunks.append(pd.DataFrame(corrupted_data_chunk))


    def run(self, mode='save_corrupted'):
        self._validate_logic()
        df_clear = pd.concat(self.clear_chunks, ignore_index=True) if self.clear_chunks else pd.DataFrame()

        if mode == 'save_corrupted' and self.corrupted_chunks:
            df_corrupted = pd.concat(self.corrupted_chunks, ignore_index=True)
            df_corrupted.to_json(self.corrupted_file_path, orient='records', lines=True, force_ascii=False)

        return df_clear