# ruff: noqa
import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'sghi-commons'
copyright = '2023, Savannah Global Health Institute'
author = 'Savannah Global Health Institute'


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinx.ext.autosummary"]

# Preserve authored syntax for defaults
autodoc_preserve_defaults = True

autodoc_default_flags = {
    'inherited-members': True,
    'show-inheritance': True,
    'special-members': ('__enter__', '__exit__', '__call__', '__getattr__', '__setattr__'),
}

autodoc_member_order = 'groupwise'

autoapi_python_use_implicit_namespaces = True

autosummary_generate = True  # Turn on sphinx.ext.autosummary

exclude_patterns = []

# Be strict about any broken references
nitpicky = True

nitpick_ignore = [
    ('py:class', 'concurrent.futures._base.Executor'),  # sphinx can't find it
    ('py:class', 'concurrent.futures._base.Future'),  # sphinx can't find it
    ('py:class', 'sghi.disposable.decorators._D'),  # private type annotations
    ('py:class', 'sghi.disposable.decorators._DE'),  # private type annotations
    ('py:class', 'sghi.disposable.decorators._P'),  # private type annotations
    ('py:class', 'sghi.disposable.decorators._R'),  # private type annotations
    ('py:class', 'sghi.disposable.decorators.not_disposed._D'),  # private type annotations
    ('py:class', 'sghi.disposable.decorators.not_disposed._DE'),  # private type annotations
    ('py:class', 'sghi.disposable.decorators.not_disposed._P'),  # private type annotations
    ('py:class', 'sghi.disposable.decorators.not_disposed._R'),  # private type annotations
    ('py:class', 'sghi.task.task._IT'),  # private type annotations
    ('py:class', 'sghi.task.task._OT'),  # private type annotations
    ('py:class', 'sghi.task.common._IT'),  # private type annotations
    ('py:class', 'sghi.task.common._OT'),  # private type annotations
    ('py:class', 'sghi.task.concurrent._IT'),  # private type annotations
    ('py:class', 'sghi.task.concurrent._OT'),  # private type annotations
    ('py:class', 'sghi.utils.checkers._Comparable'),  # private type annotations
    ('py:class', 'sghi.utils.checkers._S'),  # private type annotations
    ('py:class', 'sghi.utils.checkers._T'),  # private type annotations
    ('py:obj', 'sghi.disposable.decorators.not_disposed._P'),  # private type annotations
    ('py:obj', 'sghi.disposable.decorators.not_disposed._R'),  # private type annotations
    ('py:obj', 'sghi.task.task._IT'),  # private type annotations
    ('py:obj', 'sghi.task.task._OT'),  # private type annotations
    ('py:obj', 'sghi.task.common._IT'),  # private type annotations
    ('py:obj', 'sghi.task.common._OT'),  # private type annotations
    ('py:obj', 'sghi.task.concurrent._IT'),  # private type annotations
    ('py:obj', 'sghi.task.concurrent._OT'),  # private type annotations
]

templates_path = ['_templates']

root_doc = 'index'


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# <html_logo = "images/SGHI_Globe.png"
html_logo = "images/sghi_globe.png"

html_static_path = ['_static']

html_theme = 'furo'

html_theme_options = {
    "sidebar_hide_name": True,
    "light_css_variables": {
        "color-brand-primary": "#0474AC",  # "blue"
        "color-brand-content": "#0474AC",
    },
    "dark_css_variables": {
        "color-brand-primary": "#C1368C",  # "purple"
        "color-brand-content": "#C1368C",
    },
}


# Include Python intersphinx mapping to prevent failures
# jaraco/skeleton#51
extensions += ['sphinx.ext.intersphinx']
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pypackage': ('https://packaging.python.org/en/latest/', None),
    'importlib-resources': (
        'https://importlib-resources.readthedocs.io/en/latest',
        None,
    ),
    'django': (
        'http://docs.djangoproject.com/en/dev/',
        'http://docs.djangoproject.com/en/dev/_objects/'
    ),
}


# Support tooltips on references
extensions += ['hoverxref.extension']
hoverxref_auto_ref = True
hoverxref_intersphinx = [
    'python',
    'pip',
    'pypackage',
    'importlib-resources',
    'django',
]
