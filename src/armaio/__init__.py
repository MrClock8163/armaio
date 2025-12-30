try:
    from ._version import __version__ as __version__
except Exception:  # pragma: no coverage
    __version__ = "0.0.0"  # Placeholder value for source installs
