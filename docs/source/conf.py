"""
Configuration file for the Sphinx documentation builder.
"""

import os
import sys

# Ensure autodoc imports from the src/ layout
DOCS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(DOCS_DIR, os.pardir, os.pardir))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')

# Prepend src/ so that `dashboard_lego` can be imported during doc build
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# -- Project information -----------------------------------------------------
project = 'Dashboard Lego'
copyright = '2025, Dashboard Lego Team'
author = 'Dashboard Lego Team'
release = '1.0.0'
version = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.githubpages',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The suffix(es) of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Theme options are theme-specific and customize the look and feel of a theme
html_theme_options = {
    'analytics_id': '',  # Provided by Google Analytics
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
html_sidebars = {
    '**': [
        'relations.html',  # needs 'show_related': True theme option to display
        'searchbox.html',
    ]
}

# -- Extension configuration -------------------------------------------------

# -- Options for autodoc extension -------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Options for intersphinx extension ---------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    # External inventories below often return HTML; disable to avoid warnings
    # 'plotly': ('https://plotly.com/python-api-reference/', None),
    # 'dash': ('https://dash.plotly.com/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'sklearn': ('https://scikit-learn.org/stable/', None),
}

# -- Options for todo extension ----------------------------------------------
todo_include_todos = True

# -- MyST Parser options removed for simplicity -----------------------------

# -- Custom roles and directives ---------------------------------------------
rst_prolog = """
.. role:: python(code)
   :language: python

.. role:: bash(code)
   :language: bash

.. role:: rst(code)
   :language: rst
"""
