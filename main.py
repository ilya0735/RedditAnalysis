import re

from analyzer import Analyzer
from config import RAW_DATA_PATH, CORRUPTED_DATA_PATH, SUBREDDITS_IT, DB_URL
from downloader import Downloader
from transformer import Validator, Transformer
from loader import Loader
from visualizer import Visualizer


def sanitize_table_name(name: str) -> str:
    clean = re.sub(r"[^\w]+", "_", name.lower()).strip("_")
    return f"comments_{clean}"


def etl() -> list[str]:
    RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)
    CORRUPTED_DATA_PATH.mkdir(parents=True, exist_ok=True)

    downloader = Downloader(RAW_DATA_PATH, SUBREDDITS_IT)
    downloader.run()

    validator = Validator(batch_size=10000)
    transformer = Transformer()
    loader = Loader(DB_URL)

    created_tables = []
    for raw_file in sorted(RAW_DATA_PATH.glob("*.parquet")):
        subreddit_name = raw_file.stem
        table_name = sanitize_table_name(subreddit_name)

        corrupted_file = CORRUPTED_DATA_PATH / f"{subreddit_name}.jsonl"

        print(f"\n--- Обработка {raw_file.name} -> таблица '{table_name}' ---")

        valid_df = validator.run(raw_file, corrupted_file, mode=None)
        clean_df = transformer.run(valid_df)

        loader.run(
            df=clean_df,
            table_name=table_name,
            if_exists="replace",
        )

        created_tables.append(table_name)

    return created_tables


if __name__ == "__main__":
    tables = etl()

    print("\n>>> Запуск SQL-анализа...")
    analyzer = Analyzer(DB_URL)
    analyzer.prepare_view(tables)
    analyzer.run_all_analysis()

    print("\n>>> Генерация графиков...")
    visualizer = Visualizer(DB_URL, output_dir="data/visualization")
    visualizer.run_all_plots()