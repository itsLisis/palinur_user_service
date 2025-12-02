import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

# Import from your app
from db import Base, get_db
from main import app

# Use an in-memory SQLite DB for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create all tables in the test database
Base.metadata.create_all(bind=engine)


# Override the get_db dependency to use the testing session
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def client():
    """
    Provide a TestClient that uses the overridden dependency.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session():
    """
    Provide a SQLAlchemy session for tests (connected to the test DB).
    Tests can use this to seed data and inspect state.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
