from pathlib import Path
import pandas as pd
from pydantic import ValidationError

from validation_schema import RedditCommentSchema
from src.config import DATA_PATH


files = list(Path(DATA_PATH).glob("*.parquet"))
file_path = files[2]

if not file_path.exists():
    print(f"Файл {file_path.name} не найден.")

df = pd.read_parquet(file_path)
records = df.to_dict(orient="records")
print(1)

valid_count = 0
invalid_count = 0
for row in records:
    try:
        RedditCommentSchema.model_validate(row)
        valid_count += 1
    except ValidationError as error:
        invalid_count += 1

print(valid_count, invalid_count)

