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
    def __str__(self) -> str:
        return f"PAA - {super().__str__()}"


class PaaFormat(IntEnum):
    DXT1 = 0xff01
    DXT2 = 0xff02
    DXT3 = 0xff03
    DXT4 = 0xff04
    DXT5 = 0xff05
    RGBA4 = 0x4444
    RGBA5 = 0x1555
    RGBA8 = 0x8888
    GRAY = 0x8080


class PaaAlphaFlag(IntEnum):
    NONE = 0
    INTERPOLATED = 1
    BINARY = 2


class PaaSwizzle(IntEnum):
    ALPHA = 0
    RED = 1
    GREEN = 2
    BLUE = 3
    INVERTED_ALPHA = 4
    INVERTED_RED = 5
    INVERTED_GREEN = 6
    INVERTED_BLUE = 7
    BLANK_WHITE = 8
    BLANK_BLACK = 9


class PaaTagg(ABC):
    @classmethod
    @abstractmethod
    def read(self, stream: IO[bytes]) -> Self: ...

    @property
    @abstractmethod
    def signature(self) -> str: ...


class PaaUnknownTagg(PaaTagg):
    def __init__(self, signature: str, raw: bytes) -> None:
        self._signature = signature
        self._raw = raw

    @property
    def signature(self) -> str:
        return self._signature

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        signature = binary.read_char(stream, 8)
        length = binary.read_ulong(stream)
        data = stream.read(length)

        return cls(signature, data)


class PaaAverageColorTagg(PaaTagg):
    def __init__(self, red: int, green: int, blue: int, alpha: int) -> None:
        self._color: tuple[int, int, int, int] = (red, green, blue, alpha)

    @property
    def signature(self) -> str:
        return "GGATCGVA"

    @property
    def red(self) -> int:
        return self._color[0]

    @property
    def green(self) -> int:
        return self._color[1]

    @property
    def blue(self) -> int:
        return self._color[2]

    @property
    def alpha(self) -> int:
        return self._color[3]

    @property
    def color(self) -> tuple[int, int, int, int]:
        return self._color

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
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
    def __init__(self, red: int, green: int, blue: int, alpha: int) -> None:
        self._color: tuple[int, int, int, int] = (red, green, blue, alpha)

    @property
    def signature(self) -> str:
        return "GGATCXAM"

    @property
    def red(self) -> int:
        return self._color[0]

    @property
    def green(self) -> int:
        return self._color[1]

    @property
    def blue(self) -> int:
        return self._color[2]

    @property
    def alpha(self) -> int:
        return self._color[3]

    @property
    def color(self) -> tuple[int, int, int, int]:
        return self._color

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
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
    def __init__(self, value: PaaAlphaFlag) -> None:
        self._value = value

    @property
    def signature(self) -> str:
        return "GGATGALF"

    @property
    def value(self) -> PaaAlphaFlag:
        return self._value

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
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
    def __init__(
        self,
        red: PaaSwizzle,
        green: PaaSwizzle,
        blue: PaaSwizzle,
        alpha: PaaSwizzle
    ) -> None:
        self._commands = (red, green, blue, alpha)

    @property
    def signature(self) -> str:
        return "GGATZIWS"

    @property
    def red(self) -> PaaSwizzle:
        return self._commands[0]

    @property
    def green(self) -> PaaSwizzle:
        return self._commands[1]

    @property
    def blue(self) -> PaaSwizzle:
        return self._commands[2]

    @property
    def alpha(self) -> PaaSwizzle:
        return self._commands[3]

    @property
    def commands(self) -> tuple[
        PaaSwizzle,
        PaaSwizzle,
        PaaSwizzle,
        PaaSwizzle
    ]:
        return self._commands

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
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
    def __init__(self, offsets: tuple[int, ...]) -> None:
        self._offsets = offsets

    @property
    def signature(self) -> str:
        return "GGATSFFO"

    @property
    def offsets(self) -> tuple[int, ...]:
        return self._offsets

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
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
    def __init__(self) -> None:
        self._width: int = 0
        self._height: int = 0
        self._raw: bytes = b""
        self._lzo_compressed: bool = False

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @classmethod
    def read(
        cls,
        stream: IO[bytes]
    ) -> Self:
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
    def __init__(self) -> None:
        self._source: str = ""
        self._format: PaaFormat = PaaFormat.DXT1
        self._taggs: tuple[PaaTagg, ...] = ()
        self._mips: tuple[PaaMipmap, ...] = ()
        self._alpha: bool = False

    @property
    def source(self) -> str:
        return self._source

    @property
    def format(self) -> PaaFormat:
        return self._format

    @property
    def taggs(self) -> tuple[PaaTagg, ...]:
        return self._taggs

    @property
    def mips(self) -> tuple[PaaMipmap, ...]:
        return self._mips

    def is_alpha(self) -> bool:
        tagg = self.get_tagg(PaaFlagTagg)
        return bool(tagg and tagg.value != 0)

    @classmethod
    def read(
        cls,
        stream: IO[bytes]
    ) -> Self:
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
        output = None
        with open(filepath, "rb") as file:
            output = cls.read(file)

        output._source = filepath

        return output

    def get_tagg(
        self,
        taggtype: type[_T]
    ) -> _T | None:
        for tagg in self._taggs:
            if isinstance(tagg, taggtype):
                return tagg

        return None


def reverse_row_order(
    data: MutableSequence[float],
    width: int,
    height: int
) -> MutableSequence[float]:
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
