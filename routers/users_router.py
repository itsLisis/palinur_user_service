from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from datetime import date
from typing import List

from db import get_db
import models, schemas
from cloudinary_config import upload_image

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/complete_profile", response_model=schemas.MergeInfo)
def get_orientations_interests(db: Session = Depends(get_db)):
    
    genders = db.query(models.Gender).all()
    orientations = db.query(models.SexualOrientation).all()
    interests = db.query(models.Interest).all()

    return {
        "genders": genders,
        "sexual_orientations": orientations,
        "interests": interests
    }

@router.get("/profile", response_model=schemas.OwnProfileResponse)
def get_own_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get the profile of the authenticated user."""
    # Avoid N+1 on gender/orientation/interests/images
    profile = (
        db.query(models.Profile)
        .options(
            joinedload(models.Profile.gender),
            joinedload(models.Profile.sexual_orientation),
            joinedload(models.Profile.interests),
            joinedload(models.Profile.images),
        )
        .filter(models.Profile.id == user_id)
        .first()
    )
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Calculate age
    today = date.today()
    age = today.year - profile.birthday.year - ((today.month, today.day) < (profile.birthday.month, profile.birthday.day))
    
    # Get interests
    interests = [interest.interest_name for interest in profile.interests]
    
    # Get images
    images = [image.image_url for image in profile.images]
    image_ids = [image.id for image in profile.images]
    
    return {
        "id": profile.id,
        "username": profile.username,
        "introduction": profile.introduction,
        "age": age,
        "birthday": profile.birthday,
        "gender_id": profile.gender_id,
        "gender": profile.gender.gender_name if profile.gender else None,
        "sexual_orientation_id": profile.sexual_orientation_id,
        "sexual_orientation": profile.sexual_orientation.orientation_name if profile.sexual_orientation else None,
        "interests": interests,
        "images": images,
        "image_ids": image_ids
    }


@router.patch("/profile")
def update_profile(
    user_id: int,
    profile_data: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
):
    """
    Update profile fields for an existing profile.
    Used for editing introduction and interests from the profile tab.
    """
    profile = db.query(models.Profile).filter(models.Profile.id == user_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    # Update scalar fields
    if profile_data.username is not None:
        profile.username = profile_data.username
    if profile_data.introduction is not None:
        profile.introduction = profile_data.introduction
    if profile_data.birthday is not None:
        profile.birthday = profile_data.birthday
    if profile_data.gender_id is not None:
        profile.gender_id = profile_data.gender_id
    if profile_data.sexual_orientation_id is not None:
        profile.sexual_orientation_id = profile_data.sexual_orientation_id

    # Update interests (replace all)
    if profile_data.interest_ids is not None:
        db.query(models.UserInterest).filter(models.UserInterest.profile_id == user_id).delete(
            synchronize_session=False
        )
        for interest_id in profile_data.interest_ids:
            db.add(models.UserInterest(profile_id=user_id, interest_id=interest_id))

    db.commit()
    return {"success": True, "user_id": user_id}

@router.post("/profile/upload-image")
async def upload_profile_image(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a profile image to Cloudinary."""
    # Verify profile exists
    profile = db.query(models.Profile).filter(models.Profile.id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Check current image count
    current_images = db.query(models.ProfileImage).filter(
        models.ProfileImage.profile_id == user_id
    ).count()
    
    if current_images >= 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 6 images allowed"
        )
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Validate file size (5MB max)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size must be less than 5MB"
        )
    
    try:
        # Upload to Cloudinary
        image_url = upload_image(file_content, folder=f"profiles/{user_id}")
        
        # Save to database
        is_primary = current_images == 0
        profile_image = models.ProfileImage(
            profile_id=user_id,
            image_url=image_url,
            is_primary=is_primary
        )
        db.add(profile_image)
        db.commit()
        db.refresh(profile_image)
        
        return {
            "message": "Image uploaded successfully",
            "image_id": profile_image.id,
            "image_url": image_url,
            "is_primary": is_primary
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )

@router.delete("/profile/image/{image_id}")
def delete_profile_image(
    image_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete a profile image."""
    # Find the image
    image = db.query(models.ProfileImage).filter(
        models.ProfileImage.id == image_id,
        models.ProfileImage.profile_id == user_id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Delete from database (Cloudinary deletion is optional)
    db.delete(image)
    db.commit()
    
    return {"message": "Image deleted successfully"}

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
        gender_id=profile_data.gender_id,
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


@router.get("/profiles")
def list_all_profiles(db: Session = Depends(get_db)):
    """Return all user profiles with gender and sexual_orientation as text for matching."""
    # Avoid N+1 queries (gender/orientation/interests/images)
    profiles = (
        db.query(models.Profile)
        .options(
            joinedload(models.Profile.gender),
            joinedload(models.Profile.sexual_orientation),
            joinedload(models.Profile.interests),
            joinedload(models.Profile.images),
        )
        .all()
    )
    result = []
    for profile in profiles:
        today = date.today()
        age = today.year - profile.birthday.year - ((today.month, today.day) < (profile.birthday.month, profile.birthday.day))
        
        profile_dict = {
            "id": profile.id,
            "username": profile.username,
            "age": age,
            "introduction": profile.introduction,
            "gender": profile.gender.gender_name if profile.gender else None,
            "sexual_orientation": profile.sexual_orientation.orientation_name if profile.sexual_orientation else None,
            "sexual_orientation_id": profile.sexual_orientation_id,
            "interests": [interest.interest_name for interest in profile.interests],
            "images": [image.image_url for image in profile.images]
        }
        result.append(profile_dict)
    return result


@router.delete("/profile")
def delete_profile(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete the user's profile and related data (images, interests).
    NOTE: Cloudinary asset deletion is not handled here; only DB records.
    """
    profile = db.query(models.Profile).filter(models.Profile.id == user_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    # Remove join-table interests explicitly
    db.query(models.UserInterest).filter(models.UserInterest.profile_id == user_id).delete(
        synchronize_session=False
    )
    # Images are delete-orphan on relationship, but ensure DB cleanup
    db.query(models.ProfileImage).filter(models.ProfileImage.profile_id == user_id).delete(
        synchronize_session=False
    )

    db.delete(profile)
    db.commit()
    return {"success": True, "user_id": user_id}


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
