import math
from typing import Optional, Any

from pydantic import BaseModel, field_validator, model_validator


class RedditCommentSchema(BaseModel):
    id: str
    created_utc: str
    subreddit_name_prefixed: str

    score: int

    archived: Optional[str] = None
    author: Optional[str] = None
    author_fullname: Optional[str] = None
    body: Optional[str] = None
    comment_type: Optional[str] = None
    controversiality: Optional[str] = None
    edited: Optional[str] = None
    gilded: Optional[str] = None
    link_id: Optional[str] = None
    locked: Optional[str] = None
    name: Optional[str] = None
    parent_id: Optional[str] = None
    permalink: Optional[str] = None
    retrieved_on: Optional[str] = None
    subreddit_id: Optional[str] = None
    subreddit_type: Optional[str] = None
    total_awards_received: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def clean_pandas_nan(cls, values: Any) -> Any:
        if isinstance(values, dict):
            return {
                k: (None if (isinstance(v, float) and math.isnan(v)) else v)
                for k, v in values.items()
            }
        return values

    @field_validator('score', mode='before')
    @classmethod
    def parse_score(cls, value: Any) -> int:
        if value is None or str(value).strip() == "" or str(value).lower() == "nan":
            raise ValueError("Поле score не может быть пустым")
        try:
            score_int = int(float(value))
        except (ValueError, TypeError):
            raise ValueError(f"Невозможно конвертировать score '{value}' в целое число")

        return score_int


    @field_validator('id', 'created_utc', 'subreddit_name_prefixed', mode='before')
    @classmethod
    def check_not_empty(cls, value: Any, info) -> str:
        if value is None or str(value).strip() == "" or str(value).lower() == "nan":
            raise ValueError(f"Ключевое поле '{info.field_name}' пустое или null")
        return str(value)