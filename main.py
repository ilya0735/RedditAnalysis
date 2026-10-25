from src.downloader import Downloader

if __name__ == "__main__":
    downloader = Downloader()
    downloader.run(mode="async")

