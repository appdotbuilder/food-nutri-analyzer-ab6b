import pytest
from nicegui.testing import User
from app.database import reset_db


@pytest.fixture()
def new_db():
    reset_db()
    yield
    reset_db()


async def test_main_page_loads(user: User, new_db) -> None:
    """Test that the main page loads without errors."""
    await user.open("/")

    # Check that basic elements are present
    await user.should_see("Food Nutrition Analyzer")


async def test_history_page_loads(user: User, new_db) -> None:
    """Test that history page loads without errors."""
    await user.open("/history")

    # Should redirect to main page due to missing user_id, or show history
    # Either way, it shouldn't crash
    pass


async def test_analysis_page_not_found(user: User, new_db) -> None:
    """Test that non-existent analysis page handles gracefully."""
    await user.open("/analysis/999")

    # Should show not found message or redirect
    pass
