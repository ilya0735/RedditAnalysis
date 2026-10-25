from pathlib import Path
from src.config import DATA_PATH


class DataCleaner:
    def __init__(self, data_path: Path = DATA_PATH):
        self.data_path = Path(data_path)

    def clean_all(self, only_parquet: bool = True) -> None:
        if not self.data_path.exists():
            print(f"Папка {self.data_path} не существует.")
            return

        pattern = "*.parquet" if only_parquet else "*"
        files = [f for f in self.data_path.glob(pattern) if f.is_file()]

        if not files:
            print("В папке data нет файлов для удаления.")
            return

        freed_bytes = 0
        for file_path in files:
            try:
                size = file_path.stat().st_size
                file_path.unlink()
                freed_bytes += size
                print(f"Удален: {file_path.name} ({size:,} байт)")
            except OSError as error:
                print(f"Не удалось удалить {file_path.name}: {error}")

        print(f"Очистка завершена. Освобождено: {freed_bytes / (1024 * 1024):.2f} МБ.")

    def clean_subreddit(self, subreddit: str) -> None:
        file_path = self.data_path / f"{subreddit}.parquet"
        if file_path.exists():
            size = file_path.stat().st_size
            file_path.unlink()
            print(f"Удален: {file_path.name} ({size:,} байт)")
        else:
            print(f"Файл {file_path.name} не найден.")


cleaner = DataCleaner()
cleaner.clean_all()