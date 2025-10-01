# Makefile for Dashboard Lego documentation

.PHONY: help clean html serve check

help:
	@echo "📚 Dashboard Lego Documentation"
	@echo "─────────────────────────────────"
	@echo "Available commands:"
	@echo "  make clean    - Remove build artifacts"
	@echo "  make html     - Build HTML documentation"
	@echo "  make serve    - Build and serve docs at http://localhost:8000"
	@echo "  make check    - Check docs build without errors"
	@echo "  make all      - Clean and build documentation"

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	@echo "✅ Clean complete"

html:
	@echo "🔨 Building HTML documentation..."
	uv run sphinx-build -b html source build
	@echo "✅ Documentation built: docs/build/index.html"

check:
	@echo "🔍 Checking documentation build..."
	uv run sphinx-build -b html -W --keep-going source build
	@echo "✅ Documentation check passed"

serve: html
	@echo "🚀 Starting local server at http://localhost:8000"
	@echo "Press Ctrl+C to stop"
	cd build && python -m http.server 8000

all: clean html
	@echo "✅ Documentation built successfully!"
	@echo "📂 Open docs/build/index.html in your browser"
