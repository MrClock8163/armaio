"""
Definitions for reading PAA textures files. File writing is currently not
supported.
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
    swizzle_channels as swizzle_channels
)

from ._encoding import (  # noqa: F401
    DxtError as DxtError,
    decode_dxt1 as decode_dxt1,
    decode_dxt5 as decode_dxt5,
    decode_argb8888 as decode_argb8888,
    decode_argb1555 as decode_argb1555,
    decode_argb4444 as decode_argb4444,
    decode_ai88 as decode_ai88
)
