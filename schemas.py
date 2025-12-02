# schemas.py
from pydantic import BaseModel, field_validator
from typing import List
from datetime import date

class ProfileCreate(BaseModel):
    username: str
    introduction: str
    birthday: date
    sexual_orientation_id: int
    interest_ids: List[int] = []
    image_urls: List[str] = []
    
    @field_validator('birthday')
    def validate_age(cls, birthday):
        today = date.today()
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        
        if age < 18:
            raise ValueError('Must be at least 18 years old')
        if age > 120:
            raise ValueError('Invalid birth date')
        
        return birthday
    
    @field_validator('image_urls')
    def validate_images(cls, image_urls):
        if len(image_urls) > 6:
            raise ValueError('Maximum 6 images allowed')
        return image_urls


class ProfileUpdate(BaseModel):
    username: str | None = None
    introduction: str | None = None
    birthday: date | None = None
    sexual_orientation_id: int | None = None
    interest_ids: List[int] | None = None


class OwnProfileResponse(BaseModel):
    id: int
    username: str
    introduction: str
    age: int
    birthday: date
    sexual_orientation_id: int
    interests: List[str] = []
    images: List[str] = []
    
    class Config:
        from_attributes = True


class PublicProfileResponse(BaseModel):
    id: int
    username: str
    introduction: str
    age: int
    sexual_orientation_id: int
    interests: List[str] = []
    images: List[str] = []
    
    class Config:
        from_attributes = True

class SexualOrientationResponse(BaseModel):
    id: int
    orientation_name: str
    
    class Config:
        from_attributes = True

class InterestResponse(BaseModel):
    id: int
    interest_name: str
    
    class Config:
        from_attributes = True

class MergeInfo(BaseModel):
    sexual_orientations: List[SexualOrientationResponse]
    interests: List[InterestResponse]