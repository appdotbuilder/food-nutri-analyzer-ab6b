"""Stub for DBRX client when not available."""

import logging


class DbrxStub:
    """Stub DBRX client for testing/development."""

    def __init__(self):
        self.chat = ChatStub()


class ChatStub:
    """Stub chat completions."""

    def __init__(self):
        self.completions = CompletionsStub()


class CompletionsStub:
    """Stub completions API."""

    def create(self, **kwargs):
        """Return mock response."""
        logging.warning("Using DBRX stub - returning mock response")

        class MockChoice:
            def __init__(self):
                self.message = MockMessage()

        class MockMessage:
            def __init__(self):
                self.content = """
                {
                    "food_items": ["unknown food"],
                    "confidence_score": 0.1,
                    "nutritional_info": {
                        "calories": 0,
                        "protein_g": 0,
                        "carbohydrates_g": 0,
                        "total_fat_g": 0
                    },
                    "allergens": []
                }
                """

        class MockResponse:
            def __init__(self):
                self.choices = [MockChoice()]

        return MockResponse()


def get_dbrx_client():
    """Return stub client."""
    return DbrxStub()
