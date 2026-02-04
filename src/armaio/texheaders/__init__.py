from enum import IntEnum
from typing import NamedTuple, IO, Self, TypeVar, Generic
from dataclasses import dataclass

from .. import binary


_T = TypeVar("_T")


class TexHeadersError(Exception):
    """Exception raised upon TexHeaders file errors."""

    def __str__(self) -> str:
        return f"TEXH - {super().__str__()}"


class TexHeadersTextureFormat(IntEnum):
    INDEXED = 0
    GRAY = 1
    RGB565 = 2
    ARGB1555 = 3
    ARGB4444 = 4
    ARGB8888 = 5
    DXT1 = 6
    DXT2 = 7
    DXT3 = 8
    DXT4 = 9
    DXT5 = 10


class TexHeadersTextureSuffix(IntEnum):
    DIFFUSE = 0
    DIFFUSE_LINEAR = 1
    DETAIL = 2
    NORMAL = 3
    IRRADIANCE = 4
    RANDOM = 5
    TREECROWN = 6
    MACRO = 7
    SHADOW = 8
    SPECULAR = 9
    DITHERING = 10
    DETAIL_SPECULAR = 11
    MASK = 12
    THERMAL = 13


@dataclass(frozen=True)
class TexHeadersMipmap:
    width: int
    height: int
    format: TexHeadersTextureFormat
    offset: int

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        width, height = binary.read_ushorts(stream, 2)
        assert stream.read(2) == b"\x00\x00"  # always 0
        texformat = TexHeadersTextureFormat(binary.read_byte(stream))
        assert stream.read(1) == b"\x03"  # always 3
        offset = binary.read_ulong(stream)

        return cls(width, height, texformat, offset)

    def write(self, stream: IO[bytes]) -> None:
        binary.write_ushort(stream, self.width, self.height, 0)
        binary.write_byte(stream, self.format, 3)
        binary.write_ulong(stream, self.offset)


class TexHeadersColor(NamedTuple, Generic[_T]):
    red: _T
    green: _T
    blue: _T
    alpha: _T


def _read_rgba_float(stream: IO[bytes]) -> TexHeadersColor[float]:
    r, g, b, a = binary.read_floats(stream, 4)
    return TexHeadersColor(r, g, b, a)


def _write_rgba_float(
    stream: IO[bytes],
    color: TexHeadersColor[float]
) -> None:
    binary.write_float(
        stream,
        color.red,
        color.green,
        color.blue,
        color.alpha
    )


def _read_bgra(stream: IO[bytes]) -> TexHeadersColor[int]:
    b, g, r, a = binary.read_bytes(stream, 4)
    return TexHeadersColor(r, g, b, a)


def _write_bgra(stream: IO[bytes], color: TexHeadersColor[int]) -> None:
    binary.write_byte(
        stream,
        color.blue,
        color.green,
        color.red,
        color.alpha
    )


@dataclass(frozen=True)
class TexHeadersRecord:
    color_average_float: TexHeadersColor[float]
    color_average: TexHeadersColor[int]
    color_max: TexHeadersColor[int]
    maxcolor_defined: bool
    alpha_interpolated: bool
    alpha_binary: bool
    non_opaque: bool
    format: TexHeadersTextureFormat
    is_paa: bool
    path: str
    suffix: TexHeadersTextureSuffix
    mipmaps: tuple[TexHeadersMipmap, ...]
    filesize: int

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        count_pallets, pallet_ptr = binary.read_ulongs(stream, 2)
        if count_pallets != 1 or pallet_ptr != 0:
            raise TexHeadersError(
                "Color pallets are not supported"
            )

        average_color_float = _read_rgba_float(stream)
        average_color = _read_bgra(stream)
        max_color = _read_bgra(stream)
        clamp, transparency = binary.read_ulongs(stream, 2)
        assert clamp == 0
        assert transparency == 0xffffffff

        maxcolor_defined = binary.read_bool(stream)
        alpha_interpolated = binary.read_bool(stream)
        alpha_binary = binary.read_bool(stream)
        non_opaque = binary.read_bool(stream)

        count_mipmaps = binary.read_ulong(stream)
        format = TexHeadersTextureFormat(binary.read_ulong(stream))
        little_endian = binary.read_bool(stream)
        assert little_endian

        is_paa = binary.read_bool(stream)
        path = binary.read_asciiz(stream)
        suffix = TexHeadersTextureSuffix(binary.read_ulong(stream))
        count_mipmaps2 = binary.read_ulong(stream)
        assert count_mipmaps == count_mipmaps2

        mipmaps = tuple(
            [
                TexHeadersMipmap.read(stream)
                for _ in range(count_mipmaps)
            ]
        )
        filesize = binary.read_ulong(stream)

        return cls(
            average_color_float,
            average_color,
            max_color,
            maxcolor_defined,
            alpha_interpolated,
            alpha_binary,
            non_opaque,
            format,
            is_paa,
            path,
            suffix,
            mipmaps,
            filesize
        )

    def write(self, stream: IO[bytes]) -> None:
        binary.write_ulong(stream, 1, 0)
        _write_rgba_float(stream, self.color_average_float)
        _write_bgra(stream, self.color_average)
        _write_bgra(stream, self.color_max)
        binary.write_ulong(stream, 0, 0xffffffff)
        binary.write_bool(stream, self.maxcolor_defined)
        binary.write_bool(stream, self.alpha_interpolated)
        binary.write_bool(stream, self.alpha_binary)
        binary.write_bool(stream, self.non_opaque)
        binary.write_ulong(stream, len(self.mipmaps), self.format)
        binary.write_bool(stream, True)
        binary.write_bool(stream, self.is_paa)
        binary.write_asciiz(stream, self.path)
        binary.write_ulong(stream, self.suffix, len(self.mipmaps))
        for mip in self.mipmaps:
            mip.write(stream)

        binary.write_ulong(stream, self.filesize)


class TexHeadersFile:
    def __init__(self) -> None:
        self._textures: tuple[TexHeadersRecord, ...] = ()

    @property
    def textures(self) -> tuple[TexHeadersRecord, ...]:
        return self._textures

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        signature = stream.read(4)
        if signature != b"0DHT":
            raise TexHeadersError(
                "Not a valid TexHeaders file, unknown signature: "
                f"{signature!r}"
            )

        version = binary.read_ulong(stream)
        if version != 1:
            raise TexHeadersError(
                f"Unsupported file version: {version}"
            )

        count_textures = binary.read_ulong(stream)
        output = cls()

        output._textures = tuple(
            [
                TexHeadersRecord.read(stream)
                for _ in range(count_textures)
            ]
        )

        return output

    @classmethod
    def read_file(cls, filepath: str) -> Self:
        with open(filepath, "rb") as file:
            return cls.read(file)

    def write(self, stream: IO[bytes]) -> None:
        binary.write_chars(stream, "0DHT")
        binary.write_ulong(stream, 1, len(self._textures))
        for tex in self._textures:
            tex.write(stream)

    def write_file(self, filepath: str) -> None:
        with open(filepath, "wb") as file:
            self.write(file)
