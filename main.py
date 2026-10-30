import re
from pathlib import Path
from config import RAW_DATA_PATH, CORRUPTED_DATA_PATH, SUBREDDITS_IT, DB_URL
from downloader import Downloader
from transformer import Validator, Transformer
from loader import Loader


def sanitize_table_name(name: str) -> str:
    clean = re.sub(r"[^\w]+", "_", name.lower()).strip("_")
    return f"comments_{clean}"


def etl():
    downloader = Downloader(RAW_DATA_PATH, SUBREDDITS_IT)
    downloader.run()

    validator = Validator(batch_size=10000)
    transformer = Transformer()
    loader = Loader(DB_URL)

    for raw_file in sorted(RAW_DATA_PATH.glob("*.parquet")):
        subreddit_name = raw_file.stem
        table_name = sanitize_table_name(subreddit_name)

        corrupted_file = CORRUPTED_DATA_PATH / f"{subreddit_name}.jsonl"

        print(f"\n--- Обработка {raw_file.name} -> таблица '{table_name}' ---")

        valid_df = validator.run(raw_file, corrupted_file, mode="save_corrupted")
        clean_df = transformer.run(valid_df)

        loader.run(
            df=clean_df,
            table_name=table_name,
            if_exists="replace"
        )


if __name__ == "__main__":
    etl()

