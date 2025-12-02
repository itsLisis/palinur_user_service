# models.py
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

class Profile(Base):
    __tablename__ = "profiles"

    # Basic info
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, index=True)
    birthday = Column(Date, nullable=False)
    introduction = Column(String, nullable=False)

    # Sexual orientation
    sexual_orientation_id = Column(Integer, ForeignKey("sexual_orientations.id"), nullable=False)
    sexual_orientation = relationship("SexualOrientation", back_populates="profiles")

    # Interests
    interests = relationship("Interest", secondary="user_interests", back_populates="profiles")

    # Images
    images = relationship("ProfileImage", back_populates="profile", cascade="all, delete-orphan")


class Interest(Base):
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True, index=True)
    interest_name = Column(String, nullable=False, index=True, unique=True)

    profiles = relationship("Profile", secondary="user_interests", back_populates="interests")


class UserInterest(Base):
    __tablename__ = "user_interests"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    interest_id = Column(Integer, ForeignKey("interests.id", ondelete="CASCADE"), nullable=False)


class ProfileImage(Base):
    __tablename__ = "profile_images"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False)

    profile = relationship("Profile", back_populates="images")


class SexualOrientation(Base):
    __tablename__ = "sexual_orientations"
    
    id = Column(Integer, primary_key=True, index=True)
    orientation_name = Column(String, nullable=False, unique=True)

    profiles = relationship("Profile", back_populates="sexual_orientation")