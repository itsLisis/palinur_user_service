from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from db import get_db
import models, schemas

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/complete_profile", response_model=schemas.MergeInfo)
def get_orientations_interests(db: Session = Depends(get_db)):
    
    orientations = db.query(models.SexualOrientation).all()
    interests = db.query(models.Interest).all()
    genders = db.query(models.Gender).all()

    return {
        "sexual_orientations": orientations,
        "interests": interests,
        "genders": genders
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
        sexual_orientation_id=profile_data.sexual_orientation_id,
        gender_id=profile_data.gender_id
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


@router.get("/profiles")
def list_all_profiles(db: Session = Depends(get_db)):
    """Return all user profiles as a list of profile dicts with id, username, sexual_orientation_id, interests, and images."""
    profiles = db.query(models.Profile).all()
    result = []
    for profile in profiles:
        today = date.today()
        age = today.year - profile.birthday.year - ((today.month, today.day) < (profile.birthday.month, profile.birthday.day))
        
        profile_dict = {
            "id": profile.id,
            "username": profile.username,
            "age": age,
            "sexual_orientation_id": profile.sexual_orientation_id,
            "gender_id": profile.gender_id,
            "interests": [interest.interest_name for interest in profile.interests],
            "images": [image.image_url for image in profile.images]
        }
        result.append(profile_dict)
    return result


@router.get("/{user_id}/interests")
def get_user_interests(user_id: int, db: Session = Depends(get_db)):
    """Return the list of interest IDs for a given user."""
    profile = db.query(models.Profile).filter(models.Profile.id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Return list of interest names (or IDs, based on matching service needs)
    return [interest.interest_name for interest in profile.interests]


@router.get("/profiles/recommend/male-hetero")
def list_users_for_male_hetero(db: Session = Depends(get_db)):
    """
    Return list of user IDs recommendable for a heterosexual male.
    Criterion: sexual_orientation_id in [3, 5] (Mujer hetero, Mujer Bi)
    """
    candidates = db.query(models.Profile).filter(
        models.Profile.sexual_orientation_id.in_([3, 5])
    ).all()
    return [profile.id for profile in candidates]


@router.get("/profiles/recommend/male-homo")
def list_users_for_male_homo(db: Session = Depends(get_db)):
    """
    Return list of user IDs recommendable for a homosexual male.
    Criterion: sexual_orientation_id in [1, 2] (Hombre homo, Hombre Bi)
    """
    candidates = db.query(models.Profile).filter(
        models.Profile.sexual_orientation_id.in_([1, 2])
    ).all()
    return [profile.id for profile in candidates]


@router.get("/profiles/recommend/male-bi")
def list_users_for_male_bi(db: Session = Depends(get_db)):
    """
    Return list of user IDs recommendable for a bisexual male.
    Criterion: sexual_orientation_id in [1, 2, 3, 5] (Hombre homo, Hombre Bi, Mujer hetero, Mujer Bi)
    """
    candidates = db.query(models.Profile).filter(
        models.Profile.sexual_orientation_id.in_([1, 2, 3, 5])
    ).all()
    return [profile.id for profile in candidates]


@router.get("/profiles/recommend/female-hetero")
def list_users_for_female_hetero(db: Session = Depends(get_db)):
    """
    Return list of user IDs recommendable for a heterosexual female.
    Criterion: sexual_orientation_id in [0, 2] (Hombre hetero, Hombre Bi)
    """
    candidates = db.query(models.Profile).filter(
        models.Profile.sexual_orientation_id.in_([0, 2])
    ).all()
    return [profile.id for profile in candidates]


@router.get("/profiles/recommend/female-homo")
def list_users_for_female_homo(db: Session = Depends(get_db)):
    """
    Return list of user IDs recommendable for a homosexual female.
    Criterion: sexual_orientation_id in [4, 5] (Mujer homo, Mujer Bi)
    """
    candidates = db.query(models.Profile).filter(
        models.Profile.sexual_orientation_id.in_([4, 5])
    ).all()
    return [profile.id for profile in candidates]


@router.get("/profiles/recommend/female-bi")
def list_users_for_female_bi(db: Session = Depends(get_db)):
    """
    Return list of user IDs recommendable for a bisexual female.
    Criterion: sexual_orientation_id in [0, 1, 2, 4] (Hombre hetero, Hombre homo, Hombre Bi, Mujer homo)
    """
    candidates = db.query(models.Profile).filter(
        models.Profile.sexual_orientation_id.in_([0, 1, 2, 4])
    ).all()
    return [profile.id for profile in candidates]

