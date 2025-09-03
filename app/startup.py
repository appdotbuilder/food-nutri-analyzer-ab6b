from app.database import create_tables
import app.pages.main_page


def startup() -> None:
    # this function is called before the first request
    create_tables()

    # Register page modules
    app.pages.main_page.create()
