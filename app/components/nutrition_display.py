from nicegui import ui
from typing import List
from decimal import Decimal
from app.models import NutritionalAnalysis, AllergenDetection


class NutritionDisplayComponent:
    """Component for displaying nutritional analysis results."""

    def create_results_display(self, analysis: NutritionalAnalysis, allergen_detections: List[AllergenDetection]):
        """Create a comprehensive nutrition results display."""

        with ui.column().classes("w-full max-w-4xl mx-auto space-y-6"):
            # Header with food identification
            self._create_header(analysis)

            # Main nutrition grid
            with ui.row().classes("w-full gap-6"):
                # Left column - Main macronutrients
                with ui.column().classes("flex-1"):
                    self._create_macronutrients_card(analysis)
                    self._create_portion_info_card(analysis)

                # Right column - Micronutrients and allergens
                with ui.column().classes("flex-1"):
                    self._create_micronutrients_card(analysis)
                    self._create_allergens_card(allergen_detections)

    def _create_header(self, analysis: NutritionalAnalysis):
        """Create the header with food identification."""
        with ui.card().classes("w-full p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().classes("flex-1"):
                    ui.label("Food Analysis Results").classes("text-2xl font-bold text-gray-800")

                    if analysis.food_items:
                        food_list = ", ".join(analysis.food_items)
                        ui.label(f"Identified: {food_list}").classes("text-lg text-gray-700 mt-2")

                    if analysis.confidence_score:
                        confidence_pct = float(analysis.confidence_score * Decimal("100"))
                        color = self._get_confidence_color(confidence_pct)
                        ui.label(f"Confidence: {confidence_pct:.1f}%").classes(f"text-sm font-medium {color} mt-1")

                # Status indicator
                status_color = {
                    "completed": "bg-green-100 text-green-800",
                    "processing": "bg-blue-100 text-blue-800",
                    "failed": "bg-red-100 text-red-800",
                    "pending": "bg-yellow-100 text-yellow-800",
                }.get(analysis.status.value, "bg-gray-100 text-gray-800")

                ui.chip(analysis.status.value.title(), icon="check_circle").classes(f"{status_color}")

    def _create_macronutrients_card(self, analysis: NutritionalAnalysis):
        """Create the main macronutrients display card."""
        with ui.card().classes("w-full p-6 shadow-lg rounded-xl bg-white"):
            ui.label("Macronutrients (per 100g)").classes("text-xl font-bold text-gray-800 mb-4")

            # Calories - prominent display
            if analysis.calories:
                with ui.row().classes("items-center justify-center mb-6 p-4 bg-orange-50 rounded-lg"):
                    ui.icon("local_fire_department").classes("text-3xl text-orange-500 mr-3")
                    ui.label(f"{float(analysis.calories):.0f}").classes("text-4xl font-bold text-orange-600")
                    ui.label("calories").classes("text-lg text-gray-600 ml-2")

            # Macronutrient breakdown
            macros = [
                ("Protein", analysis.protein_g, "fitness_center", "blue"),
                ("Carbohydrates", analysis.carbohydrates_g, "grain", "green"),
                ("Total Fat", analysis.total_fat_g, "opacity", "yellow"),
                ("Saturated Fat", analysis.saturated_fat_g, "opacity", "red"),
                ("Fiber", analysis.fiber_g, "eco", "emerald"),
                ("Sugar", analysis.sugar_g, "candy", "pink"),
                ("Sodium", analysis.sodium_mg, "grain", "purple"),
            ]

            with ui.column().classes("w-full space-y-3"):
                for name, value, icon, color in macros:
                    if value is not None:
                        self._create_nutrient_row(name, value, icon, color, "mg" if "sodium" in name.lower() else "g")

    def _create_portion_info_card(self, analysis: NutritionalAnalysis):
        """Create portion information card."""
        if analysis.estimated_portion_g and analysis.total_calories:
            with ui.card().classes("w-full p-6 shadow-lg rounded-xl bg-white mt-6"):
                ui.label("Estimated Portion").classes("text-xl font-bold text-gray-800 mb-4")

                with ui.row().classes("items-center justify-between w-full"):
                    with ui.column():
                        ui.label(f"{float(analysis.estimated_portion_g):.0f}g").classes(
                            "text-2xl font-bold text-blue-600"
                        )
                        ui.label("portion size").classes("text-sm text-gray-600")

                    with ui.column():
                        ui.label(f"{float(analysis.total_calories):.0f}").classes("text-2xl font-bold text-orange-600")
                        ui.label("total calories").classes("text-sm text-gray-600")

    def _create_micronutrients_card(self, analysis: NutritionalAnalysis):
        """Create micronutrients (vitamins & minerals) card."""
        if not analysis.vitamins and not analysis.minerals:
            return

        with ui.card().classes("w-full p-6 shadow-lg rounded-xl bg-white"):
            ui.label("Vitamins & Minerals").classes("text-xl font-bold text-gray-800 mb-4")

            # Vitamins
            if analysis.vitamins:
                ui.label("Vitamins").classes("text-lg font-semibold text-gray-700 mb-2")
                with ui.column().classes("w-full space-y-2 mb-4"):
                    for vitamin, value in analysis.vitamins.items():
                        if value is not None:
                            unit = self._get_vitamin_unit(vitamin)
                            formatted_name = vitamin.replace("_", " ").title()
                            self._create_micronutrient_row(formatted_name, value, unit, "green")

            # Minerals
            if analysis.minerals:
                ui.label("Minerals").classes("text-lg font-semibold text-gray-700 mb-2")
                with ui.column().classes("w-full space-y-2"):
                    for mineral, value in analysis.minerals.items():
                        if value is not None:
                            unit = self._get_mineral_unit(mineral)
                            formatted_name = mineral.replace("_", " ").title()
                            self._create_micronutrient_row(formatted_name, value, unit, "purple")

    def _create_allergens_card(self, allergen_detections: List[AllergenDetection]):
        """Create allergens warning card."""
        if not allergen_detections:
            with ui.card().classes("w-full p-6 shadow-lg rounded-xl bg-green-50 border border-green-200 mt-6"):
                ui.label("Allergen Information").classes("text-xl font-bold text-gray-800 mb-4")
                with ui.row().classes("items-center"):
                    ui.icon("check_circle").classes("text-2xl text-green-600 mr-2")
                    ui.label("No common allergens detected").classes("text-green-700 font-medium")
            return

        with ui.card().classes("w-full p-6 shadow-lg rounded-xl bg-red-50 border border-red-200 mt-6"):
            ui.label("⚠️ Potential Allergens").classes("text-xl font-bold text-red-800 mb-4")
            ui.label("This food may contain the following allergens:").classes("text-red-700 mb-4")

            with ui.column().classes("w-full space-y-3"):
                for detection in allergen_detections:
                    if detection.allergen:
                        confidence_pct = float(detection.confidence_score * Decimal("100"))

                        with ui.row().classes("items-center p-3 bg-white rounded-lg border border-red-200"):
                            # Severity icon
                            severity_icon = self._get_severity_icon(detection.allergen.severity_level)
                            ui.icon(severity_icon).classes("text-xl text-red-600 mr-3")

                            with ui.column().classes("flex-1"):
                                ui.label(detection.allergen.name.title()).classes("font-bold text-red-800")
                                if detection.detected_in:
                                    ui.label(f"Found in: {detection.detected_in}").classes("text-sm text-red-600")
                                ui.label(f"Confidence: {confidence_pct:.1f}%").classes("text-xs text-red-500")

    def _create_nutrient_row(self, name: str, value: Decimal, icon: str, color: str, unit: str):
        """Create a row for a macronutrient."""
        color_classes = {
            "blue": "text-blue-600 bg-blue-50",
            "green": "text-green-600 bg-green-50",
            "yellow": "text-yellow-600 bg-yellow-50",
            "red": "text-red-600 bg-red-50",
            "emerald": "text-emerald-600 bg-emerald-50",
            "pink": "text-pink-600 bg-pink-50",
            "purple": "text-purple-600 bg-purple-50",
        }

        bg_color = color_classes.get(color, "text-gray-600 bg-gray-50")

        with ui.row().classes(f"items-center justify-between w-full p-3 rounded-lg {bg_color}"):
            with ui.row().classes("items-center"):
                ui.icon(icon).classes(f"text-lg {bg_color.split()[0]} mr-2")
                ui.label(name).classes("font-medium text-gray-800")

            ui.label(f"{float(value):.1f}{unit}").classes("font-bold text-gray-800")

    def _create_micronutrient_row(self, name: str, value: float, unit: str, color: str):
        """Create a row for a micronutrient."""
        with ui.row().classes("items-center justify-between w-full p-2 border-b border-gray-100"):
            ui.label(name).classes("text-gray-700")
            ui.label(f"{value:.1f}{unit}").classes(f"font-medium text-{color}-600")

    def _get_confidence_color(self, confidence: float) -> str:
        """Get color class based on confidence level."""
        if confidence >= 80:
            return "text-green-600"
        elif confidence >= 60:
            return "text-yellow-600"
        else:
            return "text-red-600"

    def _get_vitamin_unit(self, vitamin_name: str) -> str:
        """Get appropriate unit for vitamin."""
        if "mcg" in vitamin_name or "folate" in vitamin_name:
            return "mcg"
        elif "iu" in vitamin_name:
            return "IU"
        else:
            return "mg"

    def _get_mineral_unit(self, mineral_name: str) -> str:
        """Get appropriate unit for mineral."""
        return "mg"

    def _get_severity_icon(self, severity: str) -> str:
        """Get icon based on allergen severity."""
        icons = {"mild": "info", "moderate": "warning", "severe": "error"}
        return icons.get(severity, "warning")

    def create_loading_display(self):
        """Create loading display during analysis."""
        with ui.card().classes("w-full max-w-md mx-auto p-8 text-center shadow-lg rounded-xl"):
            ui.spinner(size="xl").classes("mb-6")
            ui.label("Analyzing Your Food Image").classes("text-xl font-bold text-gray-800 mb-2")
            ui.label("Our AI is identifying the food and calculating nutritional information...").classes(
                "text-gray-600 mb-4"
            )

            with (
                ui.linear_progress()
                .classes("w-full")
                .bind_value_from(ui.timer(0.1, lambda: None), "interval") as progress
            ):
                progress.set_value(0.8)  # Indeterminate progress

    def create_error_display(self, error_message: str):
        """Create error display."""
        with ui.card().classes("w-full max-w-md mx-auto p-6 bg-red-50 border border-red-200 shadow-lg rounded-xl"):
            with ui.row().classes("items-center mb-4"):
                ui.icon("error").classes("text-2xl text-red-600 mr-2")
                ui.label("Analysis Failed").classes("text-xl font-bold text-red-800")

            ui.label("We encountered an error while analyzing your food image:").classes("text-red-700 mb-2")
            ui.label(error_message).classes("text-sm text-red-600 bg-red-100 p-3 rounded mb-4")

            ui.label("Please try again with a different image or contact support if the problem persists.").classes(
                "text-red-700 text-sm"
            )
