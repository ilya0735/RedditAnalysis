from pathlib import Path
import pandas as pd
from pydantic import ValidationError

from validation_schema import RedditCommentSchema
from src.config import RAW_DATA_PATH, CORRUPTED_DATA_PATH, CLEANED_DATA_PATH

CORRUPTED_DATA_PATH.mkdir(parents=True, exist_ok=True)
CLEANED_DATA_PATH.mkdir(parents=True, exist_ok=True)

files = list(Path(RAW_DATA_PATH).glob("*.parquet"))
file_path = files[2]

if not file_path.exists():
    print(f"Файл {file_path.name} не найден.")
    raise FileNotFoundError

df = pd.read_parquet(file_path)
records = df.to_dict(orient="records")
print(1)

valid_count = 0
invalid_count = 0

corrupted_data = []
for idx, row in enumerate(records):
    try:
        RedditCommentSchema.model_validate(row)
        valid_count += 1
    except ValidationError as e:
        invalid_count += 1
        corrupted_data.append(row)

print(valid_count, invalid_count)

df_corr = pd.DataFrame(corrupted_data)

print(df_corr)



