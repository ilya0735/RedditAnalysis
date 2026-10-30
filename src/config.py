from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = BASE_DIR / "data" / "raw_data"
CORRUPTED_DATA_PATH = BASE_DIR / "data" / "corrupted_data"
CLEANED_DATA_PATH = BASE_DIR / "data" / "cleaned_data"

URL = "https://huggingface.co/api/datasets/HuggingFaceGECLM/REDDIT_comments/parquet/default/"

DB_URL = "postgresql+psycopg2://postgres:0707@localhost:5432/reddit_db"

SUBREDDITS_LIST_FULL = [
    "tifu", "explainlikeimfive", "WritingPrompts", "changemyview",
    "LifeProTips", "todayilearned", "science", "askscience",
    "ifyoulikeblank", "Foodforthought", "IWantToLearn", "bestof",
    "IAmA", "socialskills", "relationship_advice", "philosophy",
    "YouShouldKnow", "history", "books", "Showerthoughts",
    "personalfinance", "buildapc", "EatCheapAndHealthy", "boardgames",
    "malefashionadvice", "femalefashionadvice", "scifi", "Fantasy",
    "Games", "bodyweightfitness", "SkincareAddiction", "podcasts",
    "suggestmeabook", "AskHistorians", "gaming", "DIY",
    "mildlyinteresting", "sports", "space", "gadgets",
    "Documentaries", "GetMotivated", "UpliftingNews", "technology",
    "Fitness", "travel", "lifehacks", "Damnthatsinteresting",
    "gardening", "programming",
]

SUBREDDITS_IT_EXPANDED = [
    "programming", "technology", "gadgets", "buildapc",
    "gaming", "Games", "science", "askscience", "space",
    "DIY", "lifehacks", "podcasts", "explainlikeimfive", "YouShouldKnow",
]

SUBREDDITS_IT = [
    "programming",
    "technology",
    "gadgets",
    "buildapc",
]