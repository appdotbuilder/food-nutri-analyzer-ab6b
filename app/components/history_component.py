from nicegui import ui
from typing import List, Optional, Callable
from app.models import NutritionalAnalysis
from app.services.nutrition_service import NutritionAnalysisService


class HistoryComponent:
    """Component for displaying analysis history."""

    def __init__(self, on_select: Optional[Callable[[int], None]] = None):
        self.on_select = on_select
        self.nutrition_service = NutritionAnalysisService()

    def create_history_display(self, analyses: List[NutritionalAnalysis]):
        """Create history display with analysis cards."""
        if not analyses:
            self._create_empty_state()
            return

        with ui.column().classes("w-full space-y-4"):
            ui.label(f"Recent Analyses ({len(analyses)})").classes("text-xl font-bold text-gray-800 mb-4")

            for analysis in analyses:
                self._create_history_card(analysis)

    def _create_empty_state(self):
        """Create empty state when no analyses exist."""
        with ui.card().classes("w-full p-8 text-center shadow-lg rounded-xl bg-gray-50"):
            ui.icon("history").classes("text-6xl text-gray-300 mb-4")
            ui.label("No analyses yet").classes("text-xl font-semibold text-gray-600 mb-2")
            ui.label("Upload your first food image to get started!").classes("text-gray-500")

    def _create_history_card(self, analysis: NutritionalAnalysis):
        """Create a single history card."""
        # Determine card styling based on status
        status_styles = {
            "completed": "border-green-200 bg-green-50",
            "processing": "border-blue-200 bg-blue-50",
            "failed": "border-red-200 bg-red-50",
            "pending": "border-yellow-200 bg-yellow-50",
        }

        card_style = status_styles.get(analysis.status.value, "border-gray-200 bg-white")

        with ui.card().classes(
            f"w-full p-4 shadow-md rounded-lg border {card_style} hover:shadow-lg transition-shadow cursor-pointer"
        ):
            with ui.row().classes("items-start justify-between w-full"):
                # Left side - main info
                with ui.column().classes("flex-1"):
                    # Food items
                    if analysis.food_items:
                        food_text = ", ".join(analysis.food_items)
                        ui.label(food_text).classes("text-lg font-semibold text-gray-800 mb-1")
                    else:
                        ui.label("Unknown Food").classes("text-lg font-semibold text-gray-500 mb-1")

                    # Date and time
                    created_at = analysis.created_at.strftime("%b %d, %Y at %I:%M %p")
                    ui.label(created_at).classes("text-sm text-gray-600 mb-2")

                    # Key nutritional highlights (if completed)
                    if analysis.status.value == "completed":
                        with ui.row().classes("gap-4"):
                            if analysis.calories:
                                ui.chip(f"{float(analysis.calories):.0f} cal", icon="local_fire_department").classes(
                                    "bg-orange-100 text-orange-800"
                                )

                            if analysis.protein_g:
                                ui.chip(f"{float(analysis.protein_g):.1f}g protein", icon="fitness_center").classes(
                                    "bg-blue-100 text-blue-800"
                                )

                            if analysis.total_fat_g:
                                ui.chip(f"{float(analysis.total_fat_g):.1f}g fat").classes(
                                    "bg-yellow-100 text-yellow-800"
                                )

                    elif analysis.status.value == "failed" and analysis.error_message:
                        ui.label(f"Error: {analysis.error_message[:50]}...").classes("text-sm text-red-600")

                # Right side - status and actions
                with ui.column().classes("items-end"):
                    # Status badge
                    status_colors = {
                        "completed": "bg-green-100 text-green-800",
                        "processing": "bg-blue-100 text-blue-800 animate-pulse",
                        "failed": "bg-red-100 text-red-800",
                        "pending": "bg-yellow-100 text-yellow-800",
                    }

                    status_color = status_colors.get(analysis.status.value, "bg-gray-100 text-gray-800")
                    ui.chip(analysis.status.value.title()).classes(f"{status_color} mb-2")

                    # Confidence score (if available)
                    if analysis.confidence_score:
                        confidence_pct = float(analysis.confidence_score * 100)
                        confidence_color = self._get_confidence_color(confidence_pct)
                        ui.label(f"{confidence_pct:.1f}% confident").classes(f"text-xs {confidence_color}")

                    # Processing time (if available)
                    if analysis.processing_time_ms:
                        time_s = analysis.processing_time_ms / 1000
                        ui.label(f"{time_s:.1f}s").classes("text-xs text-gray-500")

            # Click handler to view full analysis
            if self.on_select and analysis.id:
                # Add click event to the card
                ui.run_javascript(f"""
                    const card = document.currentScript.previousElementSibling;
                    card.addEventListener('click', () => {{
                        // Trigger the selection callback
                        window.selectAnalysis({analysis.id});
                    }});
                """)

                # Register JavaScript function
                ui.add_head_html("""
                    <script>
                        window.selectAnalysis = function(analysisId) {
                            // This will be handled by the Python callback
                            fetch('/api/select-analysis/' + analysisId, {method: 'POST'});
                        };
                    </script>
                """)

    def _get_confidence_color(self, confidence: float) -> str:
        """Get color class based on confidence level."""
        if confidence >= 80:
            return "text-green-600"
        elif confidence >= 60:
            return "text-yellow-600"
        else:
            return "text-red-600"

    def create_compact_history(self, analyses: List[NutritionalAnalysis], limit: int = 5):
        """Create a compact history view for sidebar or dashboard."""
        recent_analyses = analyses[:limit]

        with ui.card().classes("w-full p-4 shadow-md rounded-lg bg-white"):
            with ui.row().classes("items-center justify-between mb-3"):
                ui.label("Recent Analyses").classes("text-lg font-semibold text-gray-800")
                if len(analyses) > limit:
                    ui.link(f"View all ({len(analyses)})", "/history").classes("text-blue-600 text-sm")

            if not recent_analyses:
                ui.label("No analyses yet").classes("text-gray-500 text-center py-4")
                return

            with ui.column().classes("w-full space-y-2"):
                for analysis in recent_analyses:
                    self._create_compact_analysis_item(analysis)

    def _create_compact_analysis_item(self, analysis: NutritionalAnalysis):
        """Create a compact analysis item for sidebar."""
        with ui.row().classes("items-center justify-between w-full p-2 hover:bg-gray-50 rounded"):
            with ui.column().classes("flex-1"):
                # Food name
                food_name = ", ".join(analysis.food_items) if analysis.food_items else "Unknown"
                if len(food_name) > 20:
                    food_name = food_name[:20] + "..."
                ui.label(food_name).classes("text-sm font-medium text-gray-800")

                # Date
                date_str = analysis.created_at.strftime("%m/%d")
                ui.label(date_str).classes("text-xs text-gray-600")

            # Status indicator
            status_icons = {
                "completed": ("check_circle", "text-green-600"),
                "processing": ("hourglass_empty", "text-blue-600"),
                "failed": ("error", "text-red-600"),
                "pending": ("pending", "text-yellow-600"),
            }

            icon, color = status_icons.get(analysis.status.value, ("help", "text-gray-600"))
            ui.icon(icon).classes(f"text-lg {color}")

    @ui.refreshable
    def create_refreshable_history(self):
        """Create a refreshable history component."""
        analyses = self.nutrition_service.get_recent_analyses(20)
        self.create_history_display(analyses)

    def refresh_history(self):
        """Refresh the history display."""
        if hasattr(self, "create_refreshable_history"):
            self.create_refreshable_history.refresh()
