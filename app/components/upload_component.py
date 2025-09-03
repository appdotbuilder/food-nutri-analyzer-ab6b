from nicegui import ui, events
from typing import Callable, Optional
from pathlib import Path


class ImageUploadComponent:
    """Modern image upload component with drag-and-drop and preview."""

    def __init__(self, on_upload: Callable[[bytes, str], None], on_error: Optional[Callable[[str], None]] = None):
        self.on_upload = on_upload
        self.on_error = on_error or (lambda msg: ui.notify(msg, type="negative"))
        self.preview_container = None
        self.upload_area = None

    def create(self):
        """Create the upload component UI."""
        with ui.card().classes("w-full max-w-md mx-auto p-6 bg-white shadow-lg rounded-xl"):
            ui.label("Upload Food Image").classes("text-xl font-bold text-gray-800 mb-4")
            ui.label("Take a photo or upload an image of your food for nutritional analysis").classes(
                "text-gray-600 mb-6"
            )

            # Upload area
            with ui.card().classes(
                "w-full p-8 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 transition-colors bg-gray-50"
            ):
                self.upload_area = ui.column().classes("items-center text-center")

                with self.upload_area:
                    ui.icon("cloud_upload").classes("text-4xl text-gray-400 mb-4")
                    ui.label("Drag and drop an image here").classes("text-lg text-gray-600 mb-2")
                    ui.label("or").classes("text-gray-400 mb-4")

                    with ui.row().classes("gap-4"):
                        # File upload button
                        ui.upload(
                            on_upload=self._handle_upload,
                            auto_upload=True,
                            multiple=False,
                            max_file_size=10 * 1024 * 1024,  # 10MB
                        ).classes("hidden").props("accept=image/*").mark("file_upload")

                        ui.button("Choose File", icon="folder_open", on_click=lambda: self._trigger_upload()).classes(
                            "bg-blue-500 hover:bg-blue-600 text-white px-6 py-2"
                        )

                        # Camera capture (if supported)
                        ui.button("Take Photo", icon="camera_alt", on_click=self._show_camera_capture).classes(
                            "bg-green-500 hover:bg-green-600 text-white px-6 py-2"
                        )

            # File requirements
            with ui.expansion("Supported Formats", icon="info").classes("w-full mt-4"):
                with ui.column().classes("p-4 text-sm text-gray-600"):
                    ui.label("• JPEG, PNG, WebP, BMP formats")
                    ui.label("• Maximum file size: 10MB")
                    ui.label("• Images will be automatically optimized")
                    ui.label("• For best results, ensure good lighting and clear focus")

            # Preview area (initially hidden)
            self.preview_container = ui.column().classes("w-full mt-6 hidden")

    def _trigger_upload(self):
        """Trigger the hidden file upload."""
        upload_element = None
        # Find upload element
        for element in ui.context.client.elements.values():
            if hasattr(element, "_props") and element._props.get("accept") == "image/*":
                upload_element = element
                break

        if upload_element:
            ui.run_javascript("document.querySelector('input[type=file]').click()")

    def _handle_upload(self, e: events.UploadEventArguments):
        """Handle file upload."""
        try:
            # Validate file type
            if not e.name.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
                self.on_error("Please upload a valid image file (JPEG, PNG, WebP, or BMP)")
                return

            # Validate file size
            content = e.content.read()
            if len(content) > 10 * 1024 * 1024:  # 10MB
                self.on_error("File size must be less than 10MB")
                return

            # Show preview
            self._show_preview(content, e.name)

            # Call upload handler
            self.on_upload(content, e.name)

        except Exception as ex:
            import logging

            logging.error(f"Error uploading file: {ex}")
            self.on_error(f"Error uploading file: {str(ex)}")

    def _show_preview(self, content: bytes, filename: str):
        """Show image preview."""
        if self.preview_container:
            self.preview_container.classes(remove="hidden")

            with self.preview_container:
                self.preview_container.clear()

                ui.separator().classes("my-4")
                ui.label("Image Preview").classes("text-lg font-semibold text-gray-800 mb-2")

                # Convert bytes to base64 for display
                import base64

                image_b64 = base64.b64encode(content).decode()
                mime_type = self._get_mime_type(filename)

                ui.image(f"data:{mime_type};base64,{image_b64}").classes(
                    "w-full max-w-sm mx-auto rounded-lg shadow-md"
                ).style("max-height: 300px; object-fit: contain;")

                with ui.row().classes("justify-center mt-4 gap-2"):
                    ui.chip(f"File: {filename}", icon="image").classes("bg-blue-100 text-blue-800")
                    ui.chip(f"Size: {len(content) // 1024}KB", icon="storage").classes("bg-green-100 text-green-800")

    def _show_camera_capture(self):
        """Show camera capture interface (placeholder for now)."""
        ui.notify("Camera capture feature coming soon!", type="info")
        # TODO: Implement camera capture using WebRTC or similar

    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename."""
        extension = Path(filename).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        return mime_types.get(extension, "image/jpeg")

    def show_loading(self):
        """Show loading state."""
        if self.upload_area:
            self.upload_area.clear()
            with self.upload_area:
                ui.spinner(size="lg").classes("mb-4")
                ui.label("Analyzing your food image...").classes("text-lg text-gray-600 mb-2")
                ui.label("This may take a few moments").classes("text-sm text-gray-500")

    def reset(self):
        """Reset the upload component."""
        if self.preview_container:
            self.preview_container.classes(add="hidden")
            self.preview_container.clear()

        if self.upload_area:
            self.upload_area.clear()
            with self.upload_area:
                ui.icon("cloud_upload").classes("text-4xl text-gray-400 mb-4")
                ui.label("Drag and drop an image here").classes("text-lg text-gray-600 mb-2")
                ui.label("or").classes("text-gray-400 mb-4")

                with ui.row().classes("gap-4"):
                    ui.upload(
                        on_upload=self._handle_upload, auto_upload=True, multiple=False, max_file_size=10 * 1024 * 1024
                    ).classes("hidden").props("accept=image/*")

                    ui.button("Choose File", icon="folder_open", on_click=lambda: self._trigger_upload()).classes(
                        "bg-blue-500 hover:bg-blue-600 text-white px-6 py-2"
                    )

                    ui.button("Take Photo", icon="camera_alt", on_click=self._show_camera_capture).classes(
                        "bg-green-500 hover:bg-green-600 text-white px-6 py-2"
                    )
