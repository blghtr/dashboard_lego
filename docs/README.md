# Dashboard Lego Documentation

This directory contains the Sphinx documentation for Dashboard Lego.

## Building Documentation

### Using Makefile (recommended)

```bash
cd docs

# Build and serve locally at http://localhost:8000
make serve

# Just build HTML
make html

# Clean build artifacts
make clean

# Check docs build without errors
make check

# Clean and rebuild
make all
```

### Manual build

```bash
# Generate API documentation
uv run sphinx-apidoc -o docs/source/api --separate --module-first blocks/ core/ presets/ utils/

# Build HTML
uv run sphinx-build -b html docs/source docs/build
```

## Documentation Structure

```
docs/
├── source/          # Source files (RST)
│   ├── conf.py      # Sphinx configuration
│   ├── index.rst    # Main documentation page
│   └── api/         # Auto-generated API docs
├── build/           # Generated HTML (gitignored)
└── Makefile         # Build commands
```

## Viewing Documentation

After building, open `docs/build/index.html` in your browser, or use `make serve`.

## Adding Documentation

1. **API Documentation**: Automatically generated from docstrings using `sphinx-apidoc`
2. **User Guides**: Add RST files to `source/` directory
3. **Examples**: Include code examples in RST files using `.. code-block:: python`

## Configuration

Documentation configuration is in `source/conf.py`. Key settings:

- **Extensions**: autodoc, napoleon, viewcode, intersphinx
- **Theme**: sphinx_rtd_theme (Read the Docs theme)
- **Intersphinx**: Links to Python, Pandas, Plotly, Dash, NumPy, scikit-learn

## Publishing

Documentation is **automatically published** to GitHub Pages:

1. ✅ Push to `main` branch
2. ✅ Tests pass in CI
3. ✅ Docs workflow builds and deploys automatically
4. ✅ Available at: `https://blghtr.github.io/dashboard_lego/`

**No manual publishing needed!** CI handles everything.
