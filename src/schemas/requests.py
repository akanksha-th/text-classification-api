from pydantic import BaseModel, field_validator
from src.utils.validators import get_videoId
from typing import Optional

class AnalyzeRequest(BaseModel):
    video_url: str
    max_comments: Optional[int] = 500
    
    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, v: str) -> str:
        """Validate that the URL is a valid YouTube URL"""
        video_id = get_videoId(v)
        if video_id is None:
            raise ValueError("Must be a valid YouTube URL")
        return v

    @field_validator("max_comments")
    @classmethod
    def validate_max_comments(cls, v: int) -> int:
        """Ensure max_comments is reasonable"""
        if v < 1 or v > 500:
            raise ValueError('Limit Exceeded: max_coments must be between 1 and 500')
        return v