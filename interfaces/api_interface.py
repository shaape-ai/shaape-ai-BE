from typing import Optional
from pydantic import BaseModel

class GetSizeRequest(BaseModel):
    storeId: str
    url: str
    description: str
    color: str
    title: str

class Backfill(BaseModel):
    url: str

class GetProductRequest(BaseModel):
    storeId: str
    url: str
    description: Optional[str]
    color: Optional[str]
    title: Optional[str]



class GetZaraProductImages(BaseModel):
    url: str

class GetOcassionRecommendation(BaseModel):
    description: str
    title: str

class GenerateHash(BaseModel):
    color: str
    ocassion: str
    category: str

class RecommendSize(BaseModel):
    height: str
    weight: str
    body_shape: str
    age: str

class GetRecommendation(BaseModel):
    query: str

class Chatbot(BaseModel):
    query: str
    product: Optional[GetProductRequest]
    color: Optional[str]
    ocassion: Optional[str]
    fitting: Optional[str]

class Preferences(BaseModel):
    color: str
    ocassion: str
    fitting: str

class GetOverview(BaseModel):
    product: GetProductRequest
    size_info: Optional[RecommendSize]
    preferences: Optional[Preferences]