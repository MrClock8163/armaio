# Class structure, read-write methods and conversion functions for handling
# the PAA binary data structure. Format specifications
# can be found on the community wiki (although not without errors):
# https://community.bistudio.com/wiki/PAA_File_Format


import struct
from enum import IntEnum
from io import BytesIO
from collections.abc import MutableSequence, Buffer
from copy import deepcopy
from typing import Self, TypeVar, IO
from abc import ABC, abstractmethod
from math import floor

from .. import binary
from ..compression import (
    dxt1_decompress,
    dxt5_decompress,
    lzo1x_decompress
)


class PaaError(Exception):
    """Exception raised upon PAA reader and decoding errors."""

    def __str__(self) -> str:
        return f"PAA - {super().__str__()}"


class PaaFormat(IntEnum):
    """Pixel color encoding format."""
    DXT1 = 0xff01
    """S3TC BC1/DXT1 compressed."""
    DXT2 = 0xff02
    """S3TC BC2/DXT2 compressed with premultiplied alpha."""
    DXT3 = 0xff03
    """S3TC BC2/DXT3 compressed."""
    DXT4 = 0xff04
    """S3TC BC3/DXT4 compressed with premultiplied alpha."""
    DXT5 = 0xff05
    """S3TC BC3/DXT5 compressed."""
    RGBA4 = 0x4444
    """4-bit RGBA channels."""
    RGBA5 = 0x1555
    """5-bit RGB channels with 1-bit alpha."""
    RGBA8 = 0x8888
    """8-bit RGBA channels."""
    GRAY = 0x8080
    """8-bit gray with 8-bit alpha."""


class PaaAlphaFlag(IntEnum):
    """Alpha interpolation flag."""
    NONE = 0
    """No alpha handling."""
    INTERPOLATED = 1
    """Smooth alpha."""
    BINARY = 2
    """Binary alpha."""


class PaaSwizzle(IntEnum):
    """Channel swizzling command."""
    ALPHA = 0
    """Copy to alpha channel."""
    RED = 1
    """Copy to red channel."""
    GREEN = 2
    """Copy to green channel."""
    BLUE = 3
    """Copy to blue channel."""
    INVERTED_ALPHA = 4
    """Invert and copy to alpha channel."""
    INVERTED_RED = 5
    """Invert and copy to red channel."""
    INVERTED_GREEN = 6
    """Invert and copy to green channel."""
    INVERTED_BLUE = 7
    """Invert and copy to blue channel."""
    BLANK_WHITE = 8
    """Blank over with white."""
    BLANK_BLACK = 9
    """Blank over with black."""


class PaaTagg(ABC):
    """
    Generic interface definition for TAGG types.
    """
    @classmethod
    @abstractmethod
    def read(self, stream: IO[bytes]) -> Self: ...

    @property
    @abstractmethod
    def signature(self) -> str: ...


class PaaUnknownTagg(PaaTagg):
    """
    Container for unknown TAGG data.
    """

    def __init__(self, signature: str, raw: bytes) -> None:
        """
        :param signature: TAGG name
        :type signature: str
        :param raw: Raw bytes read from file
        :type raw: bytes
        """
        self._signature = signature
        self._raw = raw

    @property
    def data(self) -> bytes:
        """
        :return: Raw data
        :rtype: bytes
        """
        return self._raw

    @property
    def signature(self) -> str:
        """
        :return: Signature string
        :rtype: str
        """
        return self._signature

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads an unknown TAGG from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :return: Read TAGG
        :rtype: Self
        """
        signature = binary.read_char(stream, 8)
        length = binary.read_ulong(stream)
        data = stream.read(length)

        return cls(signature, data)


class PaaAverageColorTagg(PaaTagg):
    """
    Container to store the average color metadata.
    """

    def __init__(self, red: int, green: int, blue: int, alpha: int) -> None:
        """
        :param red: Red component
        :type red: int
        :param green: Green component
        :type green: int
        :param blue: Blue component
        :type blue: int
        :param alpha: Alpha component
        :type alpha: int
        """
        self._color: tuple[int, int, int, int] = (red, green, blue, alpha)

    @property
    def signature(self) -> str:
        """
        :return: Signature string
        :rtype: str
        """
        return "GGATCGVA"

    @property
    def red(self) -> int:
        """
        :return: Red component
        :rtype: int
        """
        return self._color[0]

    @property
    def green(self) -> int:
        """
        :return: Green component
        :rtype: int
        """
        return self._color[1]

    @property
    def blue(self) -> int:
        """
        :return: Blue component
        :rtype: int
        """
        return self._color[2]

    @property
    def alpha(self) -> int:
        """
        :return: Alpha component
        :rtype: int
        """
        return self._color[3]

    @property
    def color(self) -> tuple[int, int, int, int]:
        """
        :return: RGBA
        :rtype: tuple[int, int, int, int]
        """
        return self._color

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads the average color metadata TAGG from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :raises PaaError: The metadata could not be read due to invalid data
        :return: Average color metadata
        :rtype: Self
        """
        signature = stream.read(8)
        if signature != b"GGATCGVA":
            raise PaaError(
                f"Invalid signature ({signature!r}) for average color tagg"
            )

        datalength = binary.read_ulong(stream)
        if datalength != 4:
            raise PaaError(
                f"Invalid data length ({datalength}) for average color tagg"
            )

        data = binary.read_ulong(stream)

        return cls(
            (data >> 1) & 255,
            (data >> 2) & 255,
            data >> 3,
            data & 255
        )


class PaaMaxColorTagg(PaaTagg):
    """
    Container to store the maximum color metadata.

    Although this is usually present in most PAA files, the actual data
    is (255, 255, 255, 255) which might not be consistent with the actual
    file contents. TexView recalculates the actual maximum color from the
    decoded image data.
    """

    def __init__(self, red: int, green: int, blue: int, alpha: int) -> None:
        """
        :param red: Red component
        :type red: int
        :param green: Green component
        :type green: int
        :param blue: Blue component
        :type blue: int
        :param alpha: Alpha component
        :type alpha: int
        """
        self._color: tuple[int, int, int, int] = (red, green, blue, alpha)

    @property
    def signature(self) -> str:
        """
        :return: Signature string
        :rtype: str
        """
        return "GGATCXAM"

    @property
    def red(self) -> int:
        """
        :return: Red component
        :rtype: int
        """
        return self._color[0]

    @property
    def green(self) -> int:
        """
        :return: Green component
        :rtype: int
        """
        return self._color[1]

    @property
    def blue(self) -> int:
        """
        :return: Blue component
        :rtype: int
        """
        return self._color[2]

    @property
    def alpha(self) -> int:
        """
        :return: Alpha component
        :rtype: int
        """
        return self._color[3]

    @property
    def color(self) -> tuple[int, int, int, int]:
        """
        :return: RGBA
        :rtype: tuple[int, int, int, int]
        """
        return self._color

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads the maximum color metadata TAGG from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :raises PaaError: The metadata could not be read due to invalid data
        :return: Maximum color metadata
        :rtype: Self
        """
        signature = stream.read(8)
        if signature != b"GGATCXAM":
            raise PaaError(
                f"Invalid signature ({signature!r}) for max color tagg"
            )

        datalength = binary.read_ulong(stream)
        if datalength != 4:
            raise PaaError(
                f"Invalid data length ({datalength}) for max color tagg"
            )

        data = binary.read_ulong(stream)

        return cls(
            (data >> 1) & 255,
            (data >> 2) & 255,
            data >> 3,
            data & 255
        )


class PaaFlagTagg(PaaTagg):
    """
    Container to store the alpha mode flag.

    This flag must be present in textures that are supposed to have
    any transparencey. If this flag is not present, the assigned model
    faces are not marked for alpha handling during the binarization of
    P3Ds.
    """

    def __init__(self, value: PaaAlphaFlag) -> None:
        """
        :param value: Alpha mode flag
        :type value: PaaAlphaFlag
        """
        self._value = value

    @property
    def signature(self) -> str:
        """
        :return: Signature string
        :rtype: str
        """
        return "GGATGALF"

    @property
    def value(self) -> PaaAlphaFlag:
        """
        :return: Alpha mode flag value
        :rtype: PaaAlphaFlag
        """
        return self._value

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads the alpha flag metadata from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :raises PaaError: The flag could not be read due to invalid data
        :return: Alpha mode flag
        :rtype: Self
        """
        signature = stream.read(8)
        if signature != b"GGATGALF":
            raise PaaError(
                f"Invalid signature ({signature!r}) for flag tagg"
            )

        datalength = binary.read_ulong(stream)
        if datalength != 4:
            raise PaaError(
                f"Invalid data length ({datalength}) for flag tagg"
            )

        flag = binary.read_ulong(stream)

        return cls(PaaAlphaFlag(flag))


class PaaSwizzleTagg(PaaTagg):
    """
    Container to store the channel swizzling commands.

    The swizzle data is ignored by the game engine, it is only used in
    TexView to reverse the swizzling done during the PNG->PAA
    conversion. It is used for the sole purpose of visual presentation to
    the users.
    """

    def __init__(
        self,
        red: PaaSwizzle,
        green: PaaSwizzle,
        blue: PaaSwizzle,
        alpha: PaaSwizzle
    ) -> None:
        """
        :param red: Red swizzle
        :type red: PaaSwizzle
        :param green: Green swizzle
        :type green: PaaSwizzle
        :param blue: Blue swizzle
        :type blue: PaaSwizzle
        :param alpha: Alpha swizzle
        :type alpha: PaaSwizzle
        """
        self._commands = (red, green, blue, alpha)

    @property
    def signature(self) -> str:
        """
        :return: Signature string
        :rtype: str
        """
        return "GGATZIWS"

    @property
    def red(self) -> PaaSwizzle:
        """
        :return: Red swizzling
        :rtype: PaaSwizzle
        """
        return self._commands[0]

    @property
    def green(self) -> PaaSwizzle:
        """
        :return: Green swizzling
        :rtype: PaaSwizzle
        """
        return self._commands[1]

    @property
    def blue(self) -> PaaSwizzle:
        """
        :return: Blue swizzling
        :rtype: PaaSwizzle
        """
        return self._commands[2]

    @property
    def alpha(self) -> PaaSwizzle:
        """
        :return: Alpha swizzling
        :rtype: PaaSwizzle
        """
        return self._commands[3]

    @property
    def commands(self) -> tuple[
        PaaSwizzle,
        PaaSwizzle,
        PaaSwizzle,
        PaaSwizzle
    ]:
        """
        RGBA channel copy commands.

        :return: RGBA swizzling
        :rtype: tuple[PaaSwizzle, ...]
        """
        return self._commands

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads the channel swizzling commands from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :raises PaaError: The swizzling could not be read due to invalid data
        :return: Channel swizzling commands
        :rtype: Self
        """
        signature = stream.read(8)
        if signature != b"GGATZIWS":
            raise PaaError(
                f"Invalid signature ({signature!r}) for swizzle tagg"
            )

        datalength = binary.read_ulong(stream)
        if datalength != 4:
            raise PaaError(
                f"Invalid data length ({datalength}) for swizzle tagg"
            )

        cmds = binary.read_bytes(stream, 4)

        return cls(
            PaaSwizzle(cmds[1]),
            PaaSwizzle(cmds[2]),
            PaaSwizzle(cmds[3]),
            PaaSwizzle(cmds[0])
        )


class PaaOffsetTagg(PaaTagg):
    """
    Container to store the byte offsets of the stored mipmaps.

    At most 16 mipmap addresses can be stored. In practice a PAA contains
    less than that.
    """

    def __init__(self, offsets: tuple[int, ...]) -> None:
        """
        :param offsets: Mipmap byte offsets from start of file
        :type offsets: tuple[int, ...]
        """
        self._offsets = offsets

    @property
    def signature(self) -> str:
        """
        :return: Signature string
        :rtype: str
        """
        return "GGATSFFO"

    @property
    def offsets(self) -> tuple[int, ...]:
        """
        :return: Offsets from beginning of file
        :rtype: tuple[int, ...]
        """
        return self._offsets

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads the 16 mipmap byte offsets from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :raises PaaError: The offsets could not be read due to invalid data
        :return: Mipmap offsets
        :rtype: Self
        """
        signature = stream.read(8)
        if signature != b"GGATSFFO":
            raise PaaError(
                f"Invalid signature ({signature!r}) for offset tagg"
            )

        datalength = binary.read_ulong(stream)
        if datalength != 64:  # 16 ulongs
            raise PaaError(
                f"Invalid data length ({datalength}) for offset tagg"
            )

        return cls(binary.read_ulongs(stream, 16))


_TAGG_SIGNATURES: dict[bytes, type[PaaTagg]] = {
    b"GGATCGVA": PaaAverageColorTagg,
    b"GGATCXAM": PaaMaxColorTagg,
    b"GGATGALF": PaaFlagTagg,
    b"GGATZIWS": PaaSwizzleTagg,
    b"GGATSFFO": PaaOffsetTagg
}


class PaaMipmap():
    """
    Texture mipmap data container.
    """

    def __init__(self) -> None:
        self._width: int = 0
        self._height: int = 0
        self._raw: bytes = b""
        self._lzo_compressed: bool = False

    @property
    def width(self) -> int:
        """
        :return: Texture width in pixels
        :rtype: int
        """
        return self._width

    @property
    def height(self) -> int:
        """
        :return: Texture height in pixels
        :rtype: int
        """
        return self._height

    @classmethod
    def read(
        cls,
        stream: IO[bytes]
    ) -> Self:
        """
        Reads a mipmap data block from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :return: Mipmap data
        :rtype: Self
        """
        output = cls()

        output._width, output._height = binary.read_ushorts(stream, 2)
        if output._width == output._height == 0:
            return output

        if output._width & 0x8000:
            output._lzo_compressed = True
            output._width ^= 0x8000

        length: int = struct.unpack('<I', stream.read(3) + b"\x00")[0]
        output._raw = stream.read(length)

        return output

    def decompress(
        self,
        format: PaaFormat
    ) -> tuple[
        MutableSequence[float],
        MutableSequence[float],
        MutableSequence[float],
        MutableSequence[float]
    ]:
        """
        Decompresses the raw mipmap pixel data according to a provided
        format.

        Additional internal conditional and unconditional compression is also
        handled.

        :param format: Data format
        :type format: PaaFormat
        :raises PaaError: Unsupported PAA format
        :return: Decompressed RGBA channel data
        :rtype: tuple[MutableSequence[float], ...]
        """
        match format:
            case PaaFormat.DXT1:
                decompressor = dxt1_decompress
                lzo_expected = self._width * self._height // 2
            case PaaFormat.DXT5:
                decompressor = dxt5_decompress
                lzo_expected = self._width * self._height
            case _:
                raise PaaError(
                    f"Unsupported format for decompression: {format}"
                )

        data: Buffer = self._raw
        if self._lzo_compressed:
            stream_lzo = BytesIO(data)
            _, data = lzo1x_decompress(stream_lzo, lzo_expected)

        stream_dxt = BytesIO(data)
        return decompressor(
            stream_dxt,
            self._width,
            self._height
        )


_T = TypeVar("_T", bound=PaaTagg)


class PaaFile():
    """
    Contaier for PAA texture format data.
    """

    def __init__(self) -> None:
        self._source: str | None = None
        self._format: PaaFormat = PaaFormat.DXT1
        self._taggs: tuple[PaaTagg, ...] = ()
        self._mips: tuple[PaaMipmap, ...] = ()
        self._alpha: bool = False

    @property
    def source(self) -> str | None:
        """
        :return: Source file path
        :rtype: str | None
        """
        return self._source

    @property
    def format(self) -> PaaFormat:
        """
        :return: Pixel data format
        :rtype: PaaFormat
        """
        return self._format

    @property
    def taggs(self) -> tuple[PaaTagg, ...]:
        """
        :return: Metadata TAGGs
        :rtype: tuple[PaaTagg, ...]
        """
        return self._taggs

    @property
    def mipmaps(self) -> tuple[PaaMipmap, ...]:
        """
        :return: Texture mipmaps
        :rtype: tuple[PaaMipmap, ...]
        """
        return self._mips

    def is_alpha(self) -> bool:
        """
        Checks if the file contains an alpha mode flag signaling
        transparency.

        :return: Texture has transparency
        :rtype: bool
        """
        tagg = self.get_tagg(PaaFlagTagg)
        return bool(tagg and tagg.value != 0)

    @classmethod
    def read(
        cls,
        stream: IO[bytes]
    ) -> Self:
        """
        Reads the file structure of a PAA texture from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :raises PaaError: Unsupported PAA format or unexpected EOF
        :return: Texture data
        :rtype: Self
        """
        output = cls()

        data_type = binary.read_ushort(stream)
        try:
            output._format = PaaFormat(data_type)
        except Exception:
            raise PaaError(f"Unknown format type: {data_type:d}")

        if output._format not in (PaaFormat.DXT1, PaaFormat.DXT5):
            raise PaaError(
                "Only DXT1 and DXT5 textures are supported, "
                f"{output._format.name} is not"
            )

        taggs: list[PaaTagg] = []
        while True:
            signature = stream.read(8)
            stream.seek(-8, 1)
            if not signature.startswith(b"GGAT"):
                break

            new_tagg = _TAGG_SIGNATURES[signature].read(stream)
            taggs.append(new_tagg)

        output._taggs = tuple(taggs)

        if binary.read_ushort(stream) != 0:
            raise PaaError("Indexed palettes are not supported")

        mipmaps: list[PaaMipmap] = []
        while True:
            mip = PaaMipmap.read(stream)
            if mip._width == mip._height == 0:
                break

            mipmaps.append(mip)

        output._mips = tuple(mipmaps)

        eof = binary.read_ushort(stream)
        if eof != 0:
            raise PaaError("Unexpected EOF value: %d" % eof)

        return output

    @classmethod
    def read_file(
        cls,
        filepath: str
    ) -> Self:
        """
        Reads a PAA file at the specified path.

        :param filepath: Path to PAA file
        :type filepath: str
        :return: Texture data
        :rtype: Self
        """
        output = None
        with open(filepath, "rb") as file:
            output = cls.read(file)

        output._source = filepath

        return output

    def get_tagg(
        self,
        taggtype: type[_T]
    ) -> _T | None:
        """
        Retrieves a TAGG of a specific type.

        If the same type of TAGG is present multiple times (does not normally
        happen in practice), the first instance is returned.

        :param taggtype: TAGG type to retrieve
        :type taggtype: type[_T]
        :return: TAGG if present
        :rtype: _T | None
        """
        for tagg in self._taggs:
            if isinstance(tagg, taggtype):
                return tagg

        return None


def reverse_row_order(
    data: MutableSequence[float],
    width: int,
    height: int
) -> MutableSequence[float]:
    """
    Reverses the row order in a flattened array of pixel data.

    :param data: Row flattened pixel data array
    :type data: MutableSequence[float]
    :param width: Texture width in pixels
    :type width: int
    :param height: Texture height in pixels
    :type height: int
    :return: Pixel data array with reveresed row order
    :rtype: MutableSequence[float]
    """
    assert len(data) == (width * height)

    new = deepcopy(data)
    for i in range(floor(height / 2)):
        new[(height-i-1)*width:(height-i)*width] = data[i*width:(i+1)*width]
        new[i*width:(i+1)*width] = data[(height-i-1)*width:(height-i)*width]

    return new


def swizzle_channels(
    red: MutableSequence[float],
    green: MutableSequence[float],
    blue: MutableSequence[float],
    alpha: MutableSequence[float],
    *,
    swizzle_red: PaaSwizzle = PaaSwizzle.RED,
    swizzle_green: PaaSwizzle = PaaSwizzle.GREEN,
    swizzle_blue: PaaSwizzle = PaaSwizzle.BLUE,
    swizzle_alpha: PaaSwizzle = PaaSwizzle.ALPHA,
    process_blanks: bool = False
) -> tuple[
    MutableSequence[float],
    MutableSequence[float],
    MutableSequence[float],
    MutableSequence[float]
]:
    """
    Process swizzling commands on a set of normalized RGBA channels.

    Example:

    .. code-block:: python

        red: MutableSequence[float] = ...
        green: MutableSequence[float] = ...
        blue: MutableSequence[float] = ...
        alpha: MutableSequence[float] = ...

        red, green, blue, alpha = swizzle_channels(
            red,
            green,
            blue,
            alpha,
            swizzle_red=PaaSwizzle.INVERTED_ALPHA
            swizzle_alpha=PaaSwizzle.INVERTED_RED
        )

    :param red: Red channel data
    :type red: MutableSequence[float]
    :param green: Green channel data
    :type green: MutableSequence[float]
    :param blue: Blue channel data
    :type blue: MutableSequence[float]
    :param alpha: Alpha channel data
    :type alpha: MutableSequence[float]
    :param swizzle_red: Red swizzle, defaults to PaaSwizzle.RED
    :type swizzle_red: PaaSwizzle, optional
    :param swizzle_green: Green swizzle, defaults to PaaSwizzle.GREEN
    :type swizzle_green: PaaSwizzle, optional
    :param swizzle_blue: Blue swizzle, defaults to PaaSwizzle.BLUE
    :type swizzle_blue: PaaSwizzle, optional
    :param swizzle_alpha: Alpha swizzle, defaults to PaaSwizzle.ALPHA
    :type swizzle_alpha: PaaSwizzle, optional
    :param process_blanks: Allow channel blanking, defaults to False
    :type process_blanks: bool, optional
    :return: Swizzled RGBA channel data
    :rtype: tuple[ MutableSequence[float], ...]


    """
    pixels = len(red)
    assert pixels == len(green) == len(blue) == len(alpha)

    sources = (alpha, red, green, blue)
    targets = deepcopy(sources)

    for command, source, channel in zip(
        (
            swizzle_alpha,
            swizzle_red,
            swizzle_green,
            swizzle_blue
        ),
        sources,
        (
            PaaSwizzle.ALPHA,
            PaaSwizzle.RED,
            PaaSwizzle.GREEN,
            PaaSwizzle.BLUE
        )
    ):
        if command is channel:
            continue

        match command:
            case (
                PaaSwizzle.ALPHA
                | PaaSwizzle.RED
                | PaaSwizzle.GREEN
                | PaaSwizzle.BLUE
            ):
                target = targets[command.value]
                for i in range(pixels):
                    target[i] = source[i]
            case (
                PaaSwizzle.INVERTED_ALPHA
                | PaaSwizzle.INVERTED_RED
                | PaaSwizzle.INVERTED_GREEN
                | PaaSwizzle.INVERTED_BLUE
            ):
                target = targets[command.value & 0b11]
                for i in range(pixels):
                    target[i] = 1 - source[i]
            case PaaSwizzle.BLANK_WHITE if process_blanks:
                target = targets[channel]
                for i in range(pixels):
                    target[i] = 1
            case PaaSwizzle.BLANK_BLACK if process_blanks:
                target = targets[channel]
                for i in range(pixels):
                    target[i] = 0

    return (*targets[1:], targets[0])
