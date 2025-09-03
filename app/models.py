from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum


class ImageSourceType(str, Enum):
    UPLOAD = "upload"
    CAMERA = "camera"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    email: str = Field(unique=True, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    food_images: List["FoodImage"] = Relationship(back_populates="user")


class FoodImage(SQLModel, table=True):
    __tablename__ = "food_images"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int = Field(gt=0)  # in bytes
    mime_type: str = Field(max_length=100, default="image/jpeg")
    source_type: ImageSourceType = Field(default=ImageSourceType.UPLOAD)
    width: Optional[int] = Field(default=None, gt=0)
    height: Optional[int] = Field(default=None, gt=0)
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="food_images")
    nutritional_analysis: Optional["NutritionalAnalysis"] = Relationship(back_populates="food_image")


class NutritionalAnalysis(SQLModel, table=True):
    __tablename__ = "nutritional_analyses"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    food_image_id: int = Field(foreign_key="food_images.id", unique=True)
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING)

    # Food identification
    food_items: List[str] = Field(default=[], sa_column=Column(JSON))
    confidence_score: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0, le=1.0)

    # Nutritional information per 100g
    calories: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    protein_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    carbohydrates_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    total_fat_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    saturated_fat_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    fiber_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    sugar_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    sodium_mg: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)

    # Estimated portion information
    estimated_portion_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    total_calories: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)

    # Additional nutritional data as JSON
    vitamins: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    minerals: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # AI analysis metadata
    ai_model_used: Optional[str] = Field(default=None, max_length=100)
    processing_time_ms: Optional[int] = Field(default=None, ge=0)
    error_message: Optional[str] = Field(default=None, max_length=1000)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    food_image: FoodImage = Relationship(back_populates="nutritional_analysis")
    allergens: List["AllergenDetection"] = Relationship(back_populates="nutritional_analysis")


class Allergen(SQLModel, table=True):
    __tablename__ = "allergens"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    severity_level: str = Field(max_length=20, default="moderate")  # mild, moderate, severe
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    detections: List["AllergenDetection"] = Relationship(back_populates="allergen")


class AllergenDetection(SQLModel, table=True):
    __tablename__ = "allergen_detections"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    nutritional_analysis_id: int = Field(foreign_key="nutritional_analyses.id")
    allergen_id: int = Field(foreign_key="allergens.id")
    confidence_score: Decimal = Field(decimal_places=2, ge=0.0, le=1.0)
    detected_in: Optional[str] = Field(default=None, max_length=200)  # specific ingredient or food item
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    nutritional_analysis: NutritionalAnalysis = Relationship(back_populates="allergens")
    allergen: Allergen = Relationship(back_populates="detections")


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    email: str = Field(max_length=255)


class UserUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = Field(default=None)


class FoodImageCreate(SQLModel, table=False):
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int = Field(gt=0)
    mime_type: str = Field(max_length=100, default="image/jpeg")
    source_type: ImageSourceType = Field(default=ImageSourceType.UPLOAD)
    width: Optional[int] = Field(default=None, gt=0)
    height: Optional[int] = Field(default=None, gt=0)
    user_id: int


class NutritionalAnalysisCreate(SQLModel, table=False):
    food_image_id: int
    food_items: List[str] = Field(default=[])
    confidence_score: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0, le=1.0)
    calories: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    protein_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    carbohydrates_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    total_fat_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    saturated_fat_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    fiber_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    sugar_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    sodium_mg: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    estimated_portion_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    vitamins: Dict[str, Any] = Field(default={})
    minerals: Dict[str, Any] = Field(default={})
    ai_model_used: Optional[str] = Field(default=None, max_length=100)


class NutritionalAnalysisUpdate(SQLModel, table=False):
    status: Optional[AnalysisStatus] = Field(default=None)
    food_items: Optional[List[str]] = Field(default=None)
    confidence_score: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0, le=1.0)
    calories: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    protein_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    carbohydrates_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    total_fat_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    saturated_fat_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    fiber_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    sugar_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    sodium_mg: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    estimated_portion_g: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    total_calories: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    vitamins: Optional[Dict[str, Any]] = Field(default=None)
    minerals: Optional[Dict[str, Any]] = Field(default=None)
    processing_time_ms: Optional[int] = Field(default=None, ge=0)
    error_message: Optional[str] = Field(default=None, max_length=1000)


class AllergenCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    severity_level: str = Field(max_length=20, default="moderate")


class AllergenDetectionCreate(SQLModel, table=False):
    nutritional_analysis_id: int
    allergen_id: int
    confidence_score: Decimal = Field(decimal_places=2, ge=0.0, le=1.0)
    detected_in: Optional[str] = Field(default=None, max_length=200)


# Response schemas for API
class UserResponse(SQLModel, table=False):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: str
    updated_at: str


class FoodImageResponse(SQLModel, table=False):
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    source_type: ImageSourceType
    width: Optional[int]
    height: Optional[int]
    created_at: str


class NutritionalAnalysisResponse(SQLModel, table=False):
    id: int
    status: AnalysisStatus
    food_items: List[str]
    confidence_score: Optional[Decimal]
    calories: Optional[Decimal]
    protein_g: Optional[Decimal]
    carbohydrates_g: Optional[Decimal]
    total_fat_g: Optional[Decimal]
    saturated_fat_g: Optional[Decimal]
    fiber_g: Optional[Decimal]
    sugar_g: Optional[Decimal]
    sodium_mg: Optional[Decimal]
    estimated_portion_g: Optional[Decimal]
    total_calories: Optional[Decimal]
    vitamins: Dict[str, Any]
    minerals: Dict[str, Any]
    ai_model_used: Optional[str]
    processing_time_ms: Optional[int]
    created_at: str
    updated_at: str


class AllergenResponse(SQLModel, table=False):
    id: int
    name: str
    description: Optional[str]
    severity_level: str
    created_at: str


class AllergenDetectionResponse(SQLModel, table=False):
    id: int
    allergen: AllergenResponse
    confidence_score: Decimal
    detected_in: Optional[str]
    created_at: str
