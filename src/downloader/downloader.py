import asyncio

from .async_downloader import AsyncDownloader
from .sync_downloader import SyncDownloader


class Downloader:
    def __init__(self):
        self.sync_downloader = SyncDownloader()
        self.async_downloader = AsyncDownloader()

    def download_sync(self):
        self.sync_downloader.download()

    def download_async(self):
        asyncio.run(self.async_downloader.download_all())

    def run(self, mode = "async"):
        if mode == "async":
            self.download_async()
        elif mode == "sync":
            self.download_sync()
        else:
            raise ValueError(f"Неизвестный режим: {mode}. Используйте 'sync' или 'async'.")