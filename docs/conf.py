import os
import sys

import requests

print(os.path.abspath(".."))
sys.path.insert(0, os.path.abspath(".."))
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Geo-Track-Analyzer"
copyright = "2023, Korbinian Schweiger"
author = "Korbinian Schweiger"
release = "0.4.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autosummary",
    "sphinx.ext.githubpages",
    "sphinx_rtd_theme",
    "sphinx_github_changelog",
]
autodoc_default_options = {"members": True, "inherited-members": True}
autosummary_generate = True
autosummary_imported_members = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

pygments_style = "sphinx"


def get_latest_tag() -> str:
    """Query GitHub API to get the most recent git tag"""
    url = "https://api.github.com/repos/kschweiger/track_analyzer/tags"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()[0]["name"]


_latest_tag = get_latest_tag()
# The short X.Y version.
version = _latest_tag
# The full version, including alpha/beta/rc tags.
release = _latest_tag

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = [
    "custom.css",
]
html_theme_options = {
    #'canonical_url': '',
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "style_nav_header_background": "#343131",
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

html_context = {
    "display_github": True,  # Integrate GitHub
    "github_user": "kschweiger",  # Username
    "github_repo": "track_analyzer",  # Repo name
    "github_version": "main",  # Version
    "conf_py_path": "/docs/",  # Path in the checkout to the docs root
}
