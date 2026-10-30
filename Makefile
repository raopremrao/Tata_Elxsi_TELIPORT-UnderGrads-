PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
STREAMLIT ?= .venv/bin/streamlit
PYTEST ?= $(PYTHON) -m pytest

.PHONY: setup test run benchmark report all clean quick-test quick-benchmark

setup:
	@echo "Setting up virtual environment and dependencies..."
	python3 -m venv .venv --system-site-packages
	$(PIP) install -r requirements.txt || pip install -r requirements.txt

test:
	@echo "Running test suite..."
	$(PYTHON) -m pytest tests/ -v || python3 -m pytest tests/ -v

quick-test:
	@echo "Running fast test suite..."
	$(PYTHON) -m pytest tests/ -v -m "not slow" || python3 -m pytest tests/ -v -m "not slow"

benchmark:
	@echo "Running multi-seed benchmark harness..."
	$(PYTHON) -m optimize.benchmark --seeds 30 || python3 -m optimize.benchmark --seeds 30

quick-benchmark:
	@echo "Running fast benchmark harness (reduced seeds)..."
	$(PYTHON) -m optimize.benchmark --seeds 3 || python3 -m optimize.benchmark --seeds 3

report:
	@echo "Generating 300 DPI PPT asset bundle and report artifacts..."
	$(PYTHON) -m reports.make_report || python3 -m reports.make_report

run:
	@echo "Starting PackForge Streamlit Dashboard on port 8501..."
	PYTHONPATH=. $(STREAMLIT) run app/Home.py --server.port 8501 || PYTHONPATH=. python3 -m streamlit run app/Home.py --server.port 8501

all: test quick-benchmark report
	@echo ""
	@echo "=========================================================="
	@echo " PackForge build and verification completed successfully! "
	@echo " Run 'make run' to launch the interactive dashboard.      "
	@echo "=========================================================="

clean:
	rm -rf __pycache__ .pytest_cache outputs/figures/* outputs/benchmark/*
