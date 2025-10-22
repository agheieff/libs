install:
	uv sync

run:
	uv run uvicorn main:app --host 0.0.0.0 --port 9000 --reload

run-from-root:
	cd .. && uv run uvicorn test_app.main:app --app-dir test_app --host 0.0.0.0 --port 9000 --reload
