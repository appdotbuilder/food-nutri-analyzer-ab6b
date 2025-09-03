import uuid
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
from io import BytesIO


class FileService:
    UPLOAD_DIR = Path("uploads")
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_SIZE = (2048, 2048)  # Max width/height

    def __init__(self):
        self.UPLOAD_DIR.mkdir(exist_ok=True)

    def validate_image_file(self, content: bytes, filename: str) -> bool:
        """Validate that the uploaded file is a valid image."""
        # Check file size
        if len(content) > self.MAX_FILE_SIZE:
            return False

        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return False

        # Try to open as image
        try:
            with Image.open(BytesIO(content)) as img:
                img.verify()
            return True
        except Exception as e:
            import logging

            logging.warning(f"Image validation failed: {e}")
            return False

    def save_image(self, content: bytes, original_filename: str) -> Tuple[str, str, int, int, int]:
        """
        Save image file and return (filename, file_path, file_size, width, height).
        Automatically resizes large images.
        """
        # Generate unique filename
        file_ext = Path(original_filename).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = self.UPLOAD_DIR / unique_filename

        # Open and potentially resize image
        with Image.open(BytesIO(content)) as img:
            # Convert to RGB if needed (for PNG with transparency, etc.)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize if too large
            if img.size[0] > self.MAX_IMAGE_SIZE[0] or img.size[1] > self.MAX_IMAGE_SIZE[1]:
                img.thumbnail(self.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

            # Save optimized image
            img.save(file_path, optimize=True, quality=85)

        # Get final file size and dimensions
        file_size = file_path.stat().st_size
        width, height = img.size

        return unique_filename, str(file_path), file_size, width, height

    def delete_image(self, file_path: str) -> bool:
        """Delete an image file. Returns True if successful."""
        try:
            Path(file_path).unlink(missing_ok=True)
            return True
        except Exception as e:
            import logging

            logging.error(f"Error deleting file {file_path}: {e}")
            return False

    def get_image_path(self, filename: str) -> Optional[str]:
        """Get the full path to an uploaded image."""
        file_path = self.UPLOAD_DIR / filename
        if file_path.exists():
            return str(file_path)
        return None
