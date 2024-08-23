from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    title: str
    youtube_video_id: str
    description: Optional[str] = None
    view_count: Optional[int] = 0
    like_count: Optional[int] = 0
    comment_count: Optional[int] = 0
    published_at: Optional[datetime] = None
    tags: List[str] = []

class VideoCreate(UserBase):
    pass

class User(UserBase):
    id: str

    class Config:
        orm_mode = True