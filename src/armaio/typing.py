from os import PathLike
from typing import TypeAlias


StrPath: TypeAlias = str | PathLike[str]
"""Path in string representation."""
BytesPath: TypeAlias = bytes | PathLike[bytes]
"""Path in bytes representation."""
StrOrBytesPath: TypeAlias = StrPath | BytesPath
"""Path in string or bytes representation."""
