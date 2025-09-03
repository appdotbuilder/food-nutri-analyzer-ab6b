import pytest
from app.services.user_service import UserService
from app.services.file_service import FileService
from app.models import UserCreate, ImageSourceType
from app.database import reset_db
from PIL import Image
from io import BytesIO


@pytest.fixture()
def new_db():
    reset_db()
    yield
    reset_db()


def test_user_service_basic_operations(new_db):
    """Test basic user service operations."""
    user_service = UserService()

    # Create user
    user_data = UserCreate(name="Test User", email="test@example.com")
    user = user_service.create_user(user_data)

    assert user.id is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"

    # Get user by email
    found_user = user_service.get_user_by_email("test@example.com")
    assert found_user is not None
    assert found_user.id == user.id


def test_file_service_basic_operations():
    """Test basic file service operations."""
    file_service = FileService()

    # Create test image
    img = Image.new("RGB", (100, 100), color="red")
    byte_arr = BytesIO()
    img.save(byte_arr, format="JPEG")
    image_bytes = byte_arr.getvalue()

    # Validate image
    is_valid = file_service.validate_image_file(image_bytes, "test.jpg")
    assert is_valid

    # Test invalid file
    is_invalid = file_service.validate_image_file(b"not an image", "test.jpg")
    assert not is_invalid


def test_image_creation_workflow(new_db):
    """Test complete workflow of creating user and image."""
    user_service = UserService()

    # Create user
    user = user_service.get_or_create_user("workflow@example.com", "Workflow User")
    assert user.id is not None

    # Create test image
    img = Image.new("RGB", (50, 50), color="blue")
    byte_arr = BytesIO()
    img.save(byte_arr, format="JPEG")
    image_bytes = byte_arr.getvalue()

    # Create food image
    food_image = user_service.create_food_image(user.id, image_bytes, "test_food.jpg", ImageSourceType.UPLOAD)

    assert food_image is not None
    assert food_image.user_id == user.id
    assert food_image.original_filename == "test_food.jpg"

    # Get user's images
    user_images = user_service.get_user_food_images(user.id)
    assert len(user_images) == 1
    assert user_images[0].id == food_image.id

    # Clean up
    user_service.file_service.delete_image(food_image.file_path)


def test_database_connectivity(new_db):
    """Test that database connection works."""
    from app.database import get_session
    from app.models import User

    with get_session() as session:
        # Create a user directly
        user = User(name="DB Test", email="db@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id is not None

        # Query it back
        from sqlmodel import select

        stmt = select(User).where(User.email == "db@example.com")
        found_user = session.exec(stmt).first()

        assert found_user is not None
        assert found_user.name == "DB Test"
