import pytest
from pathlib import Path
from PIL import Image
from io import BytesIO
from app.services.file_service import FileService


@pytest.fixture
def file_service():
    """Create FileService with temporary directory."""
    service = FileService()
    # Ensure clean state for testing
    return service


@pytest.fixture
def sample_image_bytes():
    """Create a sample JPEG image as bytes."""
    img = Image.new("RGB", (100, 100), color="red")
    byte_arr = BytesIO()
    img.save(byte_arr, format="JPEG")
    return byte_arr.getvalue()


def test_validate_and_save_image_workflow(file_service, sample_image_bytes):
    """Test complete workflow of validating and saving an image."""
    original_filename = "test_food.jpg"

    # Validate the image
    is_valid = file_service.validate_image_file(sample_image_bytes, original_filename)
    assert is_valid

    # Save the image
    filename, file_path, file_size, width, height = file_service.save_image(sample_image_bytes, original_filename)

    # Verify results
    assert filename.endswith(".jpg")
    assert Path(file_path).exists()
    assert file_size > 0
    assert width == 100
    assert height == 100

    # Verify we can retrieve the path
    retrieved_path = file_service.get_image_path(filename)
    assert retrieved_path == file_path

    # Clean up
    success = file_service.delete_image(file_path)
    assert success
    assert not Path(file_path).exists()


def test_large_image_resize_workflow(file_service):
    """Test that large images are properly resized."""
    # Create a large image
    large_img = Image.new("RGB", (3000, 2000), color="blue")
    byte_arr = BytesIO()
    large_img.save(byte_arr, format="JPEG")
    large_image_bytes = byte_arr.getvalue()

    # Validate and save
    assert file_service.validate_image_file(large_image_bytes, "large.jpg")

    filename, file_path, file_size, width, height = file_service.save_image(large_image_bytes, "large.jpg")

    # Should be resized
    assert width <= file_service.MAX_IMAGE_SIZE[0]
    assert height <= file_service.MAX_IMAGE_SIZE[1]
    assert Path(file_path).exists()

    # Clean up
    file_service.delete_image(file_path)


def test_invalid_file_rejection(file_service):
    """Test that invalid files are properly rejected."""
    invalid_data = b"This is not an image"

    # Should reject invalid data
    assert not file_service.validate_image_file(invalid_data, "test.jpg")

    # Should reject wrong extensions
    valid_image = Image.new("RGB", (50, 50), color="green")
    byte_arr = BytesIO()
    valid_image.save(byte_arr, format="JPEG")
    image_bytes = byte_arr.getvalue()

    assert not file_service.validate_image_file(image_bytes, "test.txt")
    assert not file_service.validate_image_file(image_bytes, "test.pdf")


def test_file_size_limit(file_service):
    """Test file size validation."""
    # Create content larger than max size
    oversized_data = b"x" * (file_service.MAX_FILE_SIZE + 1)

    assert not file_service.validate_image_file(oversized_data, "test.jpg")


def test_rgba_to_rgb_conversion(file_service):
    """Test conversion of RGBA images to RGB."""
    # Create PNG with transparency
    rgba_img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    byte_arr = BytesIO()
    rgba_img.save(byte_arr, format="PNG")
    rgba_bytes = byte_arr.getvalue()

    # Validate and save
    assert file_service.validate_image_file(rgba_bytes, "transparent.png")

    filename, file_path, file_size, width, height = file_service.save_image(rgba_bytes, "transparent.png")

    # Verify conversion
    saved_img = Image.open(file_path)
    assert saved_img.mode == "RGB"

    # Clean up
    file_service.delete_image(file_path)


def test_nonexistent_file_operations(file_service):
    """Test operations on nonexistent files."""
    # Getting path of nonexistent file
    assert file_service.get_image_path("nonexistent.jpg") is None

    # Deleting nonexistent file should not error
    assert file_service.delete_image("/path/that/does/not/exist.jpg")


def test_upload_directory_management(tmp_path, monkeypatch):
    """Test upload directory creation and management."""
    # Use temporary directory
    test_upload_dir = tmp_path / "test_uploads"

    # Temporarily change the upload directory
    original_upload_dir = FileService.UPLOAD_DIR
    FileService.UPLOAD_DIR = test_upload_dir

    try:
        # Create service - should create directory
        service = FileService()
        assert test_upload_dir.exists()
        assert test_upload_dir.is_dir()

        # Create a test image
        img = Image.new("RGB", (50, 50), color="blue")
        byte_arr = BytesIO()
        img.save(byte_arr, format="JPEG")
        image_bytes = byte_arr.getvalue()

        # Save image
        filename, file_path, _, _, _ = service.save_image(image_bytes, "test.jpg")

        # Verify file is in correct directory
        assert Path(file_path).parent == test_upload_dir
        assert test_upload_dir / filename == Path(file_path)

        # Clean up
        service.delete_image(file_path)

    finally:
        # Restore original directory
        FileService.UPLOAD_DIR = original_upload_dir
