"""
Definitions for reading PAA textures files. File writing is currently not
supported.

The provided classes and functions can read the structure of DXT1 and DXT5
compressed PAA texture files.
"""

from ._format import (  # noqa: F401
    PaaError as PaaError,
    PaaFormat as PaaFormat,
    PaaAlphaFlag as PaaAlphaFlag,
    PaaSwizzle as PaaSwizzle,
    PaaTagg as PaaTagg,
    PaaUnknownTagg as PaaUnknownTagg,
    PaaAverageColorTagg as PaaAverageColorTagg,
    PaaMaxColorTagg as PaaMaxColorTagg,
    PaaFlagTagg as PaaFlagTagg,
    PaaSwizzleTagg as PaaSwizzleTagg,
    PaaOffsetTagg as PaaOffsetTagg,
    PaaMipmap as PaaMipmap,
    PaaFile as PaaFile,
    reverse_row_order as reverse_row_order,
    swizzle_channels as swizzle_channels
)

from ._encoding import (  # noqa: F401
    DxtError as DxtError,
    decode_dxt1 as decode_dxt1,
    decode_dxt5 as decode_dxt5,
    decode_rgba8888 as decode_rgba8888,
    decode_rgba5551 as decode_rgba5551,
    decode_rgba4444 as decode_rgba4444,
    decode_ia88 as decode_ia88
)
