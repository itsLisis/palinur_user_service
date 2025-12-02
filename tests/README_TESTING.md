# Testing

This repository uses FastAPI + SQLAlchemy. The provided tests use pytest and an in-memory SQLite database so they run quickly and do not require a running Postgres instance.

Quick setup

1. Install runtime requirements (if not already installed):
   pip install -r requirements.txt

2. Install testing tools:
   pip install -r requirements-dev.txt

Run tests

- Run all tests:
  pytest -q

- Run with coverage:
  pytest --cov=.

How the tests work

- tests/conftest.py creates an in-memory SQLite database and calls Base.metadata.create_all(...) so all tables are created.
- The FastAPI app dependency get_db is overridden to provide sessions from the test engine.
- tests/test_users.py seeds minimal data and exercises the GET and POST endpoints in routers/users_router.py and inspects DB state.

Notes & next steps

- For more realistic integration tests you can spin up a temporary PostgreSQL service (e.g. via Docker or GitHub Actions service containers) and point the app at that DB during tests.
- Add tests for error cases (creating a profile twice, invalid birthdays, more than 6 images, missing sexual_orientation_id, etc.).
- Consider adding factories (factory_boy) or fixtures for repeated test data.
- To run tests in CI, create a workflow that installs dependencies and runs pytest (optionally with a real Postgres service).
