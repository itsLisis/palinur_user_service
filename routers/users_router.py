from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import get_db
import models, schemas

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/complete_profile", response_model=schemas.MergeInfo)
def get_orientations_interests(db: Session = Depends(get_db)):
    
    orientations = db.query(models.SexualOrientation).all()
    interests = db.query(models.Interest).all()

    return {
        "sexual_orientations": orientations,
        "interests": interests
    }

@router.post("/complete_profile")
def create_profile(
    user_id: int,
    profile_data: schemas.ProfileCreate,
    db: Session = Depends(get_db)
):

    existing_profile = db.query(models.Profile).filter(models.Profile.id == user_id).first()
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists"
        )
    
    new_profile = models.Profile(
        id=user_id,
        username=profile_data.username,
        birthday=profile_data.birthday,
        introduction=profile_data.introduction,
        sexual_orientation_id=profile_data.sexual_orientation_id
    )
    
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    if profile_data.interest_ids:
        for interest_id in profile_data.interest_ids:
            user_interest = models.UserInterest(
                profile_id=new_profile.id,
                interest_id=interest_id
            )
            db.add(user_interest)
    
    if profile_data.image_urls:
        for idx, image_url in enumerate(profile_data.image_urls):
            profile_image = models.ProfileImage(
                profile_id=new_profile.id,
                image_url=image_url,
                is_primary=(idx == 0)
            )
            db.add(profile_image)
    
    db.commit()
    
    return {
        "message": "Profile created successfully",
        "profile_id": new_profile.id,
        "user_id": user_id
    }