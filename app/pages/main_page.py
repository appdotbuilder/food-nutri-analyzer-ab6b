from nicegui import ui, app
import asyncio
from app.services.user_service import UserService
from app.services.nutrition_service import NutritionAnalysisService
from app.components.upload_component import ImageUploadComponent
from app.components.nutrition_display import NutritionDisplayComponent
from app.components.history_component import HistoryComponent


def create():
    """Create the main food analysis page."""

    @ui.page("/")
    async def main_page():
        # Initialize services
        user_service = UserService()
        nutrition_service = NutritionAnalysisService()

        # Get or create demo user (in real app, this would be from authentication)
        await ui.context.client.connected()
        user_email = app.storage.user.get("email", "demo@foodanalyzer.com")
        user_name = app.storage.user.get("name", "Demo User")

        current_user = user_service.get_or_create_user(user_email, user_name)

        # Store user info
        if current_user.id is not None:
            app.storage.user["user_id"] = current_user.id
        app.storage.user["email"] = current_user.email
        app.storage.user["name"] = current_user.name

        # Apply modern theme
        ui.colors(
            primary="#2563eb",
            secondary="#64748b",
            accent="#10b981",
            positive="#10b981",
            negative="#ef4444",
            warning="#f59e0b",
            info="#3b82f6",
        )

        # Page header
        with ui.row().classes("w-full justify-between items-center p-4 bg-white shadow-sm"):
            with ui.row().classes("items-center"):
                ui.icon("restaurant").classes("text-3xl text-blue-600 mr-3")
                ui.label("Food Nutrition Analyzer").classes("text-2xl font-bold text-gray-800")

            # User info and navigation
            with ui.row().classes("items-center gap-4"):
                ui.label(f"Welcome, {current_user.name}").classes("text-gray-600")
                ui.button("History", icon="history", on_click=lambda: ui.navigate.to("/history")).props("flat")

        # Main content area
        with ui.row().classes("w-full min-h-screen bg-gray-50 gap-6 p-6"):
            # Left side - Upload and current analysis
            with ui.column().classes("flex-1 max-w-2xl"):
                # Create upload component
                analysis_container = ui.column().classes("w-full")

                def handle_upload(content: bytes, filename: str):
                    """Handle image upload and analysis."""
                    if current_user.id is not None:
                        asyncio.create_task(_process_upload(content, filename, current_user.id, analysis_container))

                def handle_error(message: str):
                    """Handle upload errors."""
                    ui.notify(message, type="negative")

                upload_component = ImageUploadComponent(handle_upload, handle_error)
                upload_component.create()

                # Analysis results container
                with analysis_container:
                    ui.label("Upload an image to see nutritional analysis results here").classes(
                        "text-gray-500 text-center py-8"
                    )

            # Right side - Recent history
            with ui.column().classes("w-80"):
                history_component = HistoryComponent()
                recent_analyses = nutrition_service.get_recent_analyses(5)
                history_component.create_compact_history(recent_analyses)

    async def _process_upload(content: bytes, filename: str, user_id: int, container):
        """Process uploaded image asynchronously."""
        user_service = UserService()
        nutrition_service = NutritionAnalysisService()
        nutrition_display = NutritionDisplayComponent()

        try:
            # Clear container and show loading
            with container:
                container.clear()
                nutrition_display.create_loading_display()

            # Create food image record
            from app.models import ImageSourceType

            food_image = user_service.create_food_image(user_id, content, filename, ImageSourceType.UPLOAD)

            if not food_image:
                with container:
                    container.clear()
                    nutrition_display.create_error_display("Failed to save image. Please try again.")
                return

            ui.notify(f"Image uploaded successfully! Analyzing {filename}...", type="positive")

            # Analyze the image
            if food_image.id is not None:
                analysis = nutrition_service.analyze_food_image(food_image.id)

                if analysis and analysis.id is not None:
                    # Get allergen detections
                    analysis_with_allergens = nutrition_service.get_analysis_with_allergens(analysis.id)

                    if analysis_with_allergens:
                        analysis, allergen_detections = analysis_with_allergens

                        # Update display with results
                        with container:
                            container.clear()
                            if analysis.status.value == "completed":
                                nutrition_display.create_results_display(analysis, allergen_detections)
                                ui.notify("Analysis complete!", type="positive")
                            else:
                                error_msg = analysis.error_message or "Unknown error occurred"
                                nutrition_display.create_error_display(error_msg)
                    else:
                        with container:
                            container.clear()
                            nutrition_display.create_error_display("Failed to load analysis results.")
                else:
                    with container:
                        container.clear()
                        nutrition_display.create_error_display("Failed to analyze image. Please try again.")

        except Exception as e:
            import logging

            logging.error(f"Error processing image: {e}")
            nutrition_display = NutritionDisplayComponent()
            with container:
                container.clear()
                nutrition_display.create_error_display(f"Unexpected error: {str(e)}")
            ui.notify(f"Error processing image: {str(e)}", type="negative")

    # History page
    @ui.page("/history")
    async def history_page():
        await ui.context.client.connected()
        user_id = app.storage.user.get("user_id")

        if not user_id:
            ui.navigate.to("/")
            return

        # Page header
        with ui.row().classes("w-full justify-between items-center p-4 bg-white shadow-sm"):
            with ui.row().classes("items-center"):
                ui.button("← Back", icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props("flat")
                ui.icon("history").classes("text-3xl text-blue-600 mr-3 ml-4")
                ui.label("Analysis History").classes("text-2xl font-bold text-gray-800")

        # Main content
        with ui.column().classes("w-full max-w-4xl mx-auto p-6"):
            nutrition_service = NutritionAnalysisService()
            analyses = nutrition_service.get_recent_analyses(50)

            history_component = HistoryComponent()
            history_component.create_history_display(analyses)

    # Individual analysis page
    @ui.page("/analysis/{analysis_id}")
    async def analysis_page(analysis_id: int):
        await ui.context.client.connected()

        nutrition_service = NutritionAnalysisService()
        analysis_with_allergens = nutrition_service.get_analysis_with_allergens(analysis_id)

        if not analysis_with_allergens:
            ui.label("Analysis not found").classes("text-xl text-center mt-10")
            ui.button("← Back to Home", on_click=lambda: ui.navigate.to("/")).classes("mt-4")
            return

        analysis, allergen_detections = analysis_with_allergens

        # Page header
        with ui.row().classes("w-full justify-between items-center p-4 bg-white shadow-sm"):
            ui.button("← Back", icon="arrow_back", on_click=lambda: ui.navigate.to("/history")).props("flat")
            ui.label("Analysis Details").classes("text-2xl font-bold text-gray-800")

        # Main content
        with ui.column().classes("w-full p-6"):
            nutrition_display = NutritionDisplayComponent()

            if analysis.status.value == "completed":
                nutrition_display.create_results_display(analysis, allergen_detections)
            elif analysis.status.value == "failed":
                error_msg = analysis.error_message or "Analysis failed"
                nutrition_display.create_error_display(error_msg)
            else:
                nutrition_display.create_loading_display()
