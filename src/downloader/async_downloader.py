import asyncio
import re
from pathlib import Path

import aiofiles
import aiohttp

from src.config import URL


class AsyncDownloader:
    def __init__(self, raw_data_path: str | Path, subreddits: list, max_concurrent: int = 4):
        self.raw_data_path = Path(raw_data_path)
        self.subreddits = subreddits
        self.max_concurrent = max_concurrent

    async def download_file(
        self, session: aiohttp.ClientSession, url: str, file_path: Path, retries: int = 5
    ):
        for attempt in range(retries):
            try:
                downloaded = file_path.stat().st_size if file_path.exists() else 0

                headers = {}
                if downloaded:
                    headers["Range"] = f"bytes={downloaded}-"

                timeout = aiohttp.ClientTimeout(total=None, sock_connect=15, sock_read=60)
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status == 416:
                        print(f"Уже скачан: {file_path} ({downloaded:,} байт)")
                        return

                    response.raise_for_status()

                    if downloaded and response.status == 206:
                        content_range = response.headers.get("Content-Range", "")
                        match = re.match(r"bytes (\d+)-(\d+)/(\d+|\*)", content_range)

                        if not match or int(match.group(1)) != downloaded:
                            raise ValueError("Некорректный Content-Range")

                        total_size = (
                            int(match.group(3)) if match.group(3) != "*" else None
                        )
                        mode = "ab"
                    else:
                        downloaded = 0
                        content_length = response.headers.get("Content-Length", "")
                        total_size = (
                            int(content_length) if content_length.isdigit() else None
                        )
                        mode = "wb"

                    async with aiofiles.open(file_path, mode) as file:
                        async for chunk in response.content.iter_chunked(1024 * 1024):
                            await file.write(chunk)

                final_size = file_path.stat().st_size

                if total_size is not None and final_size != total_size:
                    raise OSError(
                        f"Размер не совпал: {final_size} вместо {total_size} байт"
                    )

                print(f"Скачан: {file_path} ({final_size:,} байт)")
                return

            except (aiohttp.ClientError, asyncio.TimeoutError, OSError, ValueError) as error:
                print(f"{file_path.name}: попытка {attempt + 1}/{retries}: {error}")

                if attempt == retries - 1:
                    raise

                await asyncio.sleep(attempt + 1)

    async def download_subreddit(
        self, session: aiohttp.ClientSession, subreddit: str, semaphore: asyncio.Semaphore
    ):
        async with semaphore:
            async with session.get(f"{URL}{subreddit}") as response:
                response.raise_for_status()
                data = await response.json()

            if not isinstance(data, list) or not data or not isinstance(data[0], str):
                raise ValueError(f"Некорректный ответ API для {subreddit}")

            file_path = self.raw_data_path / f"{subreddit}.parquet"
            await self.download_file(session, data[0], file_path)

    async def download_all(self):
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            tasks = [
                self.download_subreddit(session, subreddit, semaphore)
                for subreddit in self.subreddits
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for subreddit, result in zip(self.subreddits, results):
                if isinstance(result, BaseException):
                    print(f"Ошибка для {subreddit}: {result}")

    def download(self):
        asyncio.run(self.download_all())