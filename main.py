from config import RAW_DATA_PATH, CORRUPTED_DATA_PATH, SUBREDDITS_IT
from downloader import Downloader
from transformer import Validator
from transformer import Transformer

raw_file_path = RAW_DATA_PATH / 'programming.parquet'
corrupted_file_path = CORRUPTED_DATA_PATH / 'programming.jsonl'

RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)
CORRUPTED_DATA_PATH.mkdir(parents=True, exist_ok=True)

def download_files():
    downloader = Downloader(RAW_DATA_PATH, SUBREDDITS_IT)
    downloader.run()

def transform_data():
    validator = Validator(raw_file_path, corrupted_file_path)
    valid_df = validator.run(mode=None)

    transformer = Transformer()
    clean_df = transformer.run(valid_df)

    return clean_df

if __name__ == "__main__":
    download_files()
    df = transform_data()
    print(df.head())

