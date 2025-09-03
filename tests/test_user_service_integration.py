import pytest
from PIL import Image
from io import BytesIO
from app.services.user_service import UserService
from app.models import UserCreate, UserUpdate, ImageSourceType
from app.database import reset_db


@pytest.fixture()
def new_db():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def user_service():
    return UserService()


@pytest.fixture
def sample_image_bytes():
    """Sample valid JPEG image bytes."""
    img = Image.new("RGB", (100, 100), color="red")
    byte_arr = BytesIO()
    img.save(byte_arr, format="JPEG")
    return byte_arr.getvalue()


def test_user_lifecycle(user_service, new_db):
    """Test complete user lifecycle: create, get, update."""
    # Create user
    user_data = UserCreate(name="Test User", email="test@example.com")
    user = user_service.create_user(user_data)

    assert user.id is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.is_active is True

    # Get user by email
    retrieved = user_service.get_user_by_email("test@example.com")
    assert retrieved is not None
    assert retrieved.id == user.id

    # Update user
    update_data = UserUpdate(name="Updated Name", is_active=False)
    updated = user_service.update_user(user.id, update_data)

    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.is_active is False
    assert updated.email == "test@example.com"  # Unchanged


def test_get_or_create_user_scenarios(user_service, new_db):
    """Test get_or_create_user with existing and new users."""
    # Create new user
    user1 = user_service.get_or_create_user("new@example.com", "New User")
    assert user1.id is not None
    assert user1.name == "New User"

    # Get existing user - should not create duplicate
    user2 = user_service.get_or_create_user("new@example.com", "Different Name")
    assert user2.id == user1.id
    assert user2.name == "New User"  # Original name preserved
    assert user2.email == "new@example.com"


def test_food_image_creation_workflow(user_service, new_db, sample_image_bytes):
    """Test complete food image creation workflow."""
    # Create user first
    user = user_service.get_or_create_user("foodie@example.com", "Food Lover")

    # Create food image
    food_image = user_service.create_food_image(
        user.id, sample_image_bytes, "delicious_pizza.jpg", ImageSourceType.UPLOAD
    )

    assert food_image is not None
    assert food_image.original_filename == "delicious_pizza.jpg"
    assert food_image.filename.endswith(".jpg")
    assert food_image.file_size > 0
    assert food_image.width == 100
    assert food_image.height == 100
    assert food_image.user_id == user.id
    assert food_image.source_type == ImageSourceType.UPLOAD
    assert food_image.mime_type == "image/jpeg"

    # Verify file was actually saved
    from pathlib import Path

    assert Path(food_image.file_path).exists()

    # Clean up file
    user_service.file_service.delete_image(food_image.file_path)


def test_food_image_validation_rejection(user_service, new_db):
    """Test that invalid files are rejected during image creation."""
    user = user_service.get_or_create_user("test@example.com", "Test User")

    # Try with invalid data
    invalid_data = b"Not an image file"
    food_image = user_service.create_food_image(user.id, invalid_data, "fake.jpg", ImageSourceType.UPLOAD)

    assert food_image is None


def test_user_food_images_management(user_service, new_db, sample_image_bytes):
    """Test getting and managing user's food images."""
    user = user_service.get_or_create_user("collector@example.com", "Image Collector")

    # Create multiple food images
    created_images = []
    for i in range(3):
        food_image = user_service.create_food_image(
            user.id, sample_image_bytes, f"food_{i}.jpg", ImageSourceType.UPLOAD
        )
        assert food_image is not None
        created_images.append(food_image)

    # Get user's images
    retrieved_images = user_service.get_user_food_images(user.id)

    assert len(retrieved_images) == 3
    # Should be ordered by created_at desc (most recent first)
    for i in range(len(retrieved_images) - 1):
        assert retrieved_images[i].created_at >= retrieved_images[i + 1].created_at

    # Test with limit
    limited_images = user_service.get_user_food_images(user.id, limit=2)
    assert len(limited_images) == 2

    # Test deletion
    image_to_delete = created_images[0]
    success = user_service.delete_food_image(image_to_delete.id, user.id)
    assert success is True

    # Verify deletion
    remaining_images = user_service.get_user_food_images(user.id)
    assert len(remaining_images) == 2

    # Clean up remaining files
    for image in remaining_images:
        user_service.file_service.delete_image(image.file_path)


def test_food_image_deletion_security(user_service, new_db, sample_image_bytes):
    """Test that users can only delete their own images."""
    # Create two users
    user1 = user_service.get_or_create_user("user1@example.com", "User One")
    user2 = user_service.get_or_create_user("user2@example.com", "User Two")

    # User1 creates an image
    food_image = user_service.create_food_image(user1.id, sample_image_bytes, "user1_food.jpg", ImageSourceType.UPLOAD)
    assert food_image is not None

    # User2 tries to delete User1's image - should fail
    success = user_service.delete_food_image(food_image.id, user2.id)
    assert success is False

    # User1 can delete their own image
    success = user_service.delete_food_image(food_image.id, user1.id)
    assert success is True


def test_mime_type_detection(user_service):
    """Test MIME type detection from filename."""
    test_cases = [
        ("photo.jpg", "image/jpeg"),
        ("image.jpeg", "image/jpeg"),
        ("screenshot.png", "image/png"),
        ("animated.webp", "image/webp"),
        ("bitmap.bmp", "image/bmp"),
        ("unknown.xyz", "image/jpeg"),  # Default
        ("noextension", "image/jpeg"),  # Default
    ]

    for filename, expected_mime in test_cases:
        actual_mime = user_service._get_mime_type(filename)
        assert actual_mime == expected_mime


def test_large_image_handling(user_service, new_db):
    """Test handling of large images that need resizing."""
    user = user_service.get_or_create_user("photographer@example.com", "Pro Photographer")

    # Create a large image
    large_img = Image.new("RGB", (3000, 2000), color="blue")
    byte_arr = BytesIO()
    large_img.save(byte_arr, format="JPEG")
    large_image_bytes = byte_arr.getvalue()

    # Create food image - should be automatically resized
    food_image = user_service.create_food_image(user.id, large_image_bytes, "huge_meal.jpg", ImageSourceType.UPLOAD)

    assert food_image is not None
    assert food_image.width <= user_service.file_service.MAX_IMAGE_SIZE[0]
    assert food_image.height <= user_service.file_service.MAX_IMAGE_SIZE[1]

    # Clean up
    user_service.file_service.delete_image(food_image.file_path)


def test_empty_user_images(user_service, new_db):
    """Test getting images for user with no images."""
    user = user_service.get_or_create_user("empty@example.com", "No Images")

    images = user_service.get_user_food_images(user.id)
    assert len(images) == 0


def test_user_not_found_operations(user_service, new_db):
    """Test operations with non-existent users."""
    # Get non-existent user
    user = user_service.get_user_by_email("nonexistent@example.com")
    assert user is None

    # Update non-existent user
    update_data = UserUpdate(name="New Name")
    updated = user_service.update_user(999, update_data)
    assert updated is None

    # Delete image for non-existent user/image
    success = user_service.delete_food_image(999, 999)
    assert success is False
