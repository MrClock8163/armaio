from armaio import __version__


project = 'ArmaIO'
copyright = '2025, MrClock'
author = 'MrClock'
version = ".".join(__version__.split(".")[0:2])
release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "notfound.extension",
    "sphinx_last_updated_by_git",
    "sphinx_copybutton"
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

nitpicky = True
nitpick_ignore = {
    ("py:class", "_T"),
    ("py:class", "optional"),
    ("py:class", "StrOrBytesPath"),
    ("py:class", "Image.Image")
}
nitpick_ignore_regex = {
    ("py:class", r".*numpy.*"),
    ("py:class", r".*np.*"),
    ("py:class", r".*npt.*"),
    ("py:class", r".*_T"),
}
