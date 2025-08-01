# ============================================================================
# FILE: Makefile (Development Commands)
# ============================================================================

.PHONY: test test-unit test-integration test-performance test-security
.PHONY: lint format type-check quality-check
.PHONY: install install-dev clean coverage

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-test.txt

# Testing
test: test-unit

test-unit:
	pytest tests/ -v --tb=short -m "not hardware and not slow"

test-integration:
	pytest tests/ -v --tb=short -m "hardware"

test-performance:
	pytest tests/ -v --tb=short -m "slow"

test-security:
	pytest tests/test_security.py -v

test-all:
	pytest tests/ -v --tb=short

# Coverage
coverage:
	pytest tests/ --cov=routes --cov=utils --cov=app --cov-report=html --cov-report=term-missing

# Code Quality
lint:
	flake8 routes/ utils/ app.py tests/

format:
	black .
	isort .

format-check:
	black --check .
	isort --check-only .

type-check:
	mypy routes/ utils/ --ignore-missing-imports

quality-check: lint format-check type-check

# Development
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/

# Server
dev-server:
	python app.py --debug --host 0.0.0.0 --port 5000

prod-server:
	python app.py --host 0.0.0.0 --port 5000

# Documentation
docs:
	curl http://localhost:5000/api/docs | python -m json.tool

# Quick development cycle
dev: quality-check test-unit
	@echo "✅ Development checks passed!"

# Full CI pipeline
ci: install-dev quality-check test-all coverage
	@echo "✅ All CI checks passed!"