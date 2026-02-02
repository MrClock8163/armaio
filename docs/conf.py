from armaio import __version__


project = 'ArmaIO'
copyright = '2025-%Y, ArmaIO contributors'
author = 'MrClock'
version = ".".join(__version__.split(".")[0:2])
release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "notfound.extension",
    "sphinx_last_updated_by_git",
    "sphinx_copybutton",
    "sphinx_mdinclude"
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pillow": ("https://pillow.readthedocs.io/en/latest", None),
    "numpy": ("https://numpy.org/doc/stable", None)
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'furo'
html_static_path = ['_static']
html_copy_source = False
html_favicon = "_static/favicon.svg"
html_logo = "_static/favicon.svg"

nitpicky = True
nitpick_ignore = {
    ("py:class", "_T"),
    ("py:class", "optional"),
    ("py:class", "numpy.uint8")
}
nitpick_ignore_regex = {
    ("py:class", r".*_T")
}

autodoc_default_options = {
    "member-order": "groupwise",
    "members": True
}
autoclass_content = "both"
