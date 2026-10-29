import asyncio
from pathlib import Path

from .async_downloader import AsyncDownloader
from .sync_downloader import SyncDownloader


class Downloader:
    def __init__(self, raw_data_path: str | Path, subreddits: list):
        self.raw_data_path = Path(raw_data_path)
        self.subreddits = subreddits
        self.sync_downloader = SyncDownloader(self.raw_data_path, self.subreddits)
        self.async_downloader = AsyncDownloader(self.raw_data_path, self.subreddits)

    def download_sync(self) -> None:
        self.sync_downloader.download()

    def download_async(self) -> None:
        asyncio.run(self.async_downloader.download_all())

    def run(self, mode: str = "async") -> None:
        if mode == "async":
            self.download_async()
        elif mode == "sync":
            self.download_sync()
        else:
            raise ValueError(f"Неизвестный режим: {mode}. Используйте 'sync' или 'async'.")