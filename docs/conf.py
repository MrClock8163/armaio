from armaio import __version__

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ArmaIO'
copyright = '2025, MrClock'
author = 'MrClock'
version = ".".join(__version__.split(".")[0:2])
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "notfound.extension",
    "sphinx_last_updated_by_git"
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None)
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']

nitpicky = True
nitpick_ignore = {
    ("py:class", "optional")
}


# GitHub source linking
def linkcode_resolve(domain: str, info: dict[str, str]) -> str | None:
    if domain != 'py':
        return None
    if not info['module']:
        return None
    filename = info['module'].replace('.', '/')
    return (
        "https://github.com/MrClock8163/"
        f"armaio/tree/main/src/{filename:s}.py"
    )
