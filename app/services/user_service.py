from typing import Optional, List
from sqlmodel import select
from app.database import get_session
from app.models import User, FoodImage, UserCreate, UserUpdate, ImageSourceType
from app.services.file_service import FileService


class UserService:
    """Service for managing users and their food images."""

    def __init__(self):
        self.file_service = FileService()

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        with get_session() as session:
            user = User(**user_data.model_dump())
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        with get_session() as session:
            stmt = select(User).where(User.email == email)
            return session.exec(stmt).first()

    def get_or_create_user(self, email: str, name: str) -> User:
        """Get existing user or create new one."""
        user = self.get_user_by_email(email)
        if user:
            return user

        user_data = UserCreate(name=name, email=email)
        return self.create_user(user_data)

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return None

            update_dict = user_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(user, field, value)

            session.commit()
            session.refresh(user)
            return user

    def create_food_image(
        self,
        user_id: int,
        content: bytes,
        original_filename: str,
        source_type: ImageSourceType = ImageSourceType.UPLOAD,
    ) -> Optional[FoodImage]:
        """Create a new food image record after saving the file."""
        # Validate and save the image file
        if not self.file_service.validate_image_file(content, original_filename):
            return None

        try:
            filename, file_path, file_size, width, height = self.file_service.save_image(content, original_filename)

            # Get MIME type
            mime_type = self._get_mime_type(original_filename)

            # Create database record
            with get_session() as session:
                food_image = FoodImage(
                    filename=filename,
                    original_filename=original_filename,
                    file_path=file_path,
                    file_size=file_size,
                    mime_type=mime_type,
                    source_type=source_type,
                    width=width,
                    height=height,
                    user_id=user_id,
                )
                session.add(food_image)
                session.commit()
                session.refresh(food_image)
                return food_image

        except Exception as e:
            import logging

            logging.error(f"Error creating food image: {e}")
            return None

    def get_user_food_images(self, user_id: int, limit: int = 20) -> List[FoodImage]:
        """Get user's food images, most recent first."""
        with get_session() as session:
            from sqlmodel import desc

            stmt = (
                select(FoodImage).where(FoodImage.user_id == user_id).order_by(desc(FoodImage.created_at)).limit(limit)
            )
            return list(session.exec(stmt).all())

    def delete_food_image(self, image_id: int, user_id: int) -> bool:
        """Delete a food image (only if it belongs to the user)."""
        with get_session() as session:
            stmt = select(FoodImage).where(FoodImage.id == image_id, FoodImage.user_id == user_id)
            food_image = session.exec(stmt).first()

            if not food_image:
                return False

            # Delete the physical file
            self.file_service.delete_image(food_image.file_path)

            # Delete from database
            session.delete(food_image)
            session.commit()
            return True

    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename extension."""
        extension = filename.lower().split(".")[-1] if "." in filename else ""

        mime_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "bmp": "image/bmp",
        }

        return mime_types.get(extension, "image/jpeg")
