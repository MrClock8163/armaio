from enum import IntEnum
from typing import NamedTuple, IO, Self, TypeVar, Generic
from dataclasses import dataclass
from pathlib import Path
import os
from re import compile

from .. import binary
from ..paa import (
    PaaFile,
    PaaFormat,
    PaaAverageColorTagg,
    PaaMaxColorTagg,
    PaaFlagTagg,
    PaaOffsetTagg,
    PaaAlphaFlag
)


_T = TypeVar("_T")


class TexHeadersError(Exception):
    """Exception raised upon TexHeaders file errors."""

    def __str__(self) -> str:
        return f"TEXH - {super().__str__()}"


class TexHeadersTextureFormat(IntEnum):
    """Pixel color encoding."""
    INDEXED = 0
    """Palette indexed."""
    GRAY = 1
    """8-bit gray with 8-bit alpha."""
    RGB565 = 2
    """5-bit red and green channels with 6-bit green channel."""
    ARGB1555 = 3
    """5-bit RGB channels with 1-bit alpha."""
    ARGB4444 = 4
    """4-bit RGBA channels."""
    ARGB8888 = 5
    """8-bit RGBA channels."""
    DXT1 = 6
    """S3TC BC1/DXT1 compressed."""
    DXT2 = 7
    """S3TC BC2/DXT2 compressed with premultiplied alpha."""
    DXT3 = 8
    """S3TC BC2/DXT3 compressed."""
    DXT4 = 9
    """S3TC BC3/DXT4 compressed with premultiplied alpha."""
    DXT5 = 10
    """S3TC BC3/DXT5 compressed."""


_FORMAT_MAP: dict[PaaFormat, TexHeadersTextureFormat] = {
    PaaFormat.ARGB1555: TexHeadersTextureFormat.ARGB1555,
    PaaFormat.ARGB4444: TexHeadersTextureFormat.ARGB4444,
    PaaFormat.ARGB8888: TexHeadersTextureFormat.ARGB8888,
    PaaFormat.GRAY: TexHeadersTextureFormat.GRAY,
    PaaFormat.DXT1: TexHeadersTextureFormat.DXT1,
    PaaFormat.DXT2: TexHeadersTextureFormat.DXT2,
    PaaFormat.DXT3: TexHeadersTextureFormat.DXT3,
    PaaFormat.DXT4: TexHeadersTextureFormat.DXT4,
    PaaFormat.DXT5: TexHeadersTextureFormat.DXT5
}


class TexHeadersTextureSuffix(IntEnum):
    """Texture suffix type."""
    DIFFUSE = 0
    """Diffuse color in sRGB space."""
    DIFFUSE_LINEAR = 1
    """Diffuse color in linear space (``_sky``, ``_lco``, etc.)."""
    DETAIL = 2
    """Detail texture in linear space (``_dt``, ``_cdt``, etc.)."""
    NORMAL = 3
    """Normal map."""
    IRRADIANCE = 4
    """Irradiance map."""
    RANDOM = 5
    """Random or procedural values."""
    TREECROWN = 6
    """Treecrown texture."""
    MACRO = 7
    """Macro overlay texture in sRGB space (``_mc``, etc.)."""
    SHADOW = 8
    """Ambient shadow map (``_as``, etc.)."""
    SPECULAR = 9
    """Specular map (``_sm``, ``_smdi``, etc.)."""
    DITHERING = 10
    """Dithering map."""
    DETAIL_SPECULAR = 11
    """Detail specular map (``_dtsmdi``)."""
    MASK = 12
    """Multi material mask (``_mask``)."""
    THERMAL = 13
    """Thermal imaging texture (``_ti``)."""


_SUFFIX_MAP: dict[str, TexHeadersTextureSuffix] = {
    **dict.fromkeys(
        [
            "co",
            "ca",
            "cat",
            "can",
        ],
        TexHeadersTextureSuffix.DIFFUSE
    ),
    **dict.fromkeys(
        [
            "sky",
            "lco",
            "lca"
        ],
        TexHeadersTextureSuffix.DIFFUSE_LINEAR
    ),
    **dict.fromkeys(
        [
            "dt",
            "detail",
            "cdt",
            "mco"
        ],
        TexHeadersTextureSuffix.DETAIL
    ),
    **dict.fromkeys(
        [
            "no",
            "nopx",
            "noex",
            "normalmap",
            "ns",
            "nsex",
            "nshq",
            "nof",
            "nofex",
            "nofhq",
            "non",
            "nohq",
            "novhq"
        ],
        TexHeadersTextureSuffix.NORMAL
    ),
    "mc": TexHeadersTextureSuffix.MACRO,
    **dict.fromkeys(
        [
            "as",
            "ads",
            "adshq"
        ],
        TexHeadersTextureSuffix.SHADOW
    ),
    **dict.fromkeys(
        [
            "sm",
            "smdi"
        ],
        TexHeadersTextureSuffix.SPECULAR
    ),
    "dtsmdi": TexHeadersTextureSuffix.DETAIL_SPECULAR,
    "mask": TexHeadersTextureSuffix.MASK,
    "ti": TexHeadersTextureSuffix.THERMAL
}


def _get_suffix(filepath: Path) -> TexHeadersTextureSuffix:
    name = filepath.stem.lower()
    if name.endswith("_ti_ca"):
        return TexHeadersTextureSuffix.THERMAL

    return _SUFFIX_MAP.get(
        name.split("_")[-1].lower(),
        TexHeadersTextureSuffix.DIFFUSE
    )


class TexHeadersColor(NamedTuple, Generic[_T]):
    """RGBA color value."""
    red: _T
    """Red value."""
    green: _T
    """Green value."""
    blue: _T
    """Blue value."""
    alpha: _T
    """Alpha value."""


@dataclass(frozen=True)
class TexHeadersMipmap:
    """Texture mipmap record."""
    width: int
    """Texture width."""
    height: int
    """Texture height."""
    format: TexHeadersTextureFormat
    """Pixel color encoding."""
    offset: int
    """Byte offset to mipmap in texture file."""

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads a mipmap record from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :return: Mipmap data
        :rtype: Self
        """
        width, height = binary.read_ushorts(stream, 2)
        assert stream.read(2) == b"\x00\x00"  # always 0
        texformat = TexHeadersTextureFormat(binary.read_byte(stream))
        assert stream.read(1) == b"\x03"  # always 3
        offset = binary.read_ulong(stream)

        return cls(width, height, texformat, offset)

    def write(self, stream: IO[bytes]) -> None:
        """
        Writes a mipmap record to a binary stream.

        :param stream: Target binary stream
        :type stream: IO[bytes]
        """
        binary.write_ushort(stream, self.width, self.height, 0)
        binary.write_byte(stream, self.format, 3)
        binary.write_ulong(stream, self.offset)


def _read_rgba_float(stream: IO[bytes]) -> TexHeadersColor[float]:
    """
    Reads an RGBA color encoded as floats from a binary stream.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: Color value
    :rtype: TexHeadersColor[float]
    """
    r, g, b, a = binary.read_floats(stream, 4)
    return TexHeadersColor(r, g, b, a)


def _write_rgba_float(
    stream: IO[bytes],
    color: TexHeadersColor[float]
) -> None:
    """
    Writes an RGBA color encoded as floats to a binary stream.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param color: RGBA color in [0.0; 1.0] range
    :type color: TexHeadersColor[float]
    """
    binary.write_float(
        stream,
        color.red,
        color.green,
        color.blue,
        color.alpha
    )


def _read_bgra(stream: IO[bytes]) -> TexHeadersColor[int]:
    """
    Reads an RGBA color encoded as integers from a binary stream.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: Color value
    :rtype: TexHeadersColor[float]
    """
    b, g, r, a = binary.read_bytes(stream, 4)
    return TexHeadersColor(r, g, b, a)


def _write_bgra(stream: IO[bytes], color: TexHeadersColor[int]) -> None:
    """
    Writes an RGBA color encoded as integers to a binary stream.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param color: RGBA color in [0; 255] range
    :type color: TexHeadersColor[float]
    """
    binary.write_byte(
        stream,
        color.blue,
        color.green,
        color.red,
        color.alpha
    )


@dataclass(frozen=True)
class TexHeadersRecord:
    """Texture data record."""
    color_average_float: TexHeadersColor[float]
    """Float encoded average texture color."""
    color_average: TexHeadersColor[int]
    """8-bit average texture color."""
    color_max: TexHeadersColor[int]
    """8-bit maximum texture color."""
    maxcolor_defined: bool
    """Texture has maximum color TAGG."""
    alpha_interpolated: bool
    """Alpha channel is interpolated for smooth transparency."""
    alpha_binary: bool
    """Alpha channel is not interpolated, simple transparency."""
    non_opaque: bool
    """Interpolated alpha and average alpha is below 127."""
    format: TexHeadersTextureFormat
    """Pixel color encoding."""
    is_paa: bool
    """File is a PAA (not PAC)."""
    path: str
    """Path to texture file relative to ``texHeaders.bin`` file."""
    suffix: TexHeadersTextureSuffix
    """Texture type."""
    mipmaps: tuple[TexHeadersMipmap, ...]
    """Mipmap records."""
    filesize: int
    """File size in bytes."""

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads a texture record from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :raises TexHeadersError: Color palette indexed file data was found
        :return: Texture data
        :rtype: Self
        """
        count_palettes, palette_ptr = binary.read_ulongs(stream, 2)
        if count_palettes != 1 or palette_ptr != 0:
            raise TexHeadersError(
                "Color palettes are not supported"
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
        """
        Writes a texture record to a binary stream.

        :param stream: Target binary stream
        :type stream: IO[bytes]
        """
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

    @classmethod
    def from_paa(
        cls,
        filepath: str | os.PathLike[str],
        root: str | os.PathLike[str],
        paa: PaaFile
    ) -> Self:
        """
        Creates a texture record from PAA data.

        :param filepath: Path to the PAA file
        :type filepath: str | os.PathLike[str]
        :param root: Path to root texture index file
        :type root: str | os.PathLike[str]
        :param paa: Texture data
        :type paa: PaaFile
        :raises TexHeadersError: PAA data did not contain the necessary data
        :return: Texture record
        :rtype: Self
        """
        avg_color = paa.get_tagg(PaaAverageColorTagg)
        if avg_color is None:
            raise TexHeadersError(
                "Average color TAGG not found in PAA"
            )

        color_avg = TexHeadersColor(
            avg_color.red,
            avg_color.green,
            avg_color.blue,
            avg_color.alpha
        )
        color_avg_float = TexHeadersColor(
            color_avg.red / 255,
            color_avg.green / 255,
            color_avg.blue / 255,
            color_avg.alpha / 255
        )

        max_color = paa.get_tagg(PaaMaxColorTagg)
        if max_color is None:
            color_max = TexHeadersColor(255, 255, 255, 255)
            max_defined = False
        else:
            color_max = TexHeadersColor(
                max_color.red,
                max_color.green,
                max_color.blue,
                max_color.alpha
            )
            max_defined = True

        offsets = paa.get_tagg(PaaOffsetTagg)
        if offsets is None:
            raise TexHeadersError(
                "Mipmap offsets TAGG not found in PAA"
            )

        mipmaps = [
            TexHeadersMipmap(
                mip.width,
                mip.height,
                _FORMAT_MAP[paa.format],
                offset
            )
            for mip, offset in zip(paa.mipmaps, offsets.offsets)
        ]

        filepath = Path(filepath)
        root = Path(root)

        flag = paa.get_tagg(PaaFlagTagg)
        size = filepath.stat().st_size

        return cls(
            color_avg_float,
            color_avg,
            color_max,
            max_defined,
            bool(flag is not None and flag.value == PaaAlphaFlag.INTERPOLATED),
            bool(flag is not None and flag.value == PaaAlphaFlag.BINARY),
            bool(
                flag is not None
                and flag.value == PaaAlphaFlag.INTERPOLATED
                and color_avg.alpha < 128
            ),
            _FORMAT_MAP[paa.format],
            True,
            str(filepath.relative_to(root)).lower().replace("/", "\\"),
            _get_suffix(filepath),
            tuple(mipmaps),
            size
        )


class TexHeadersFile:
    """Texture index file."""

    def __init__(self) -> None:
        self._textures: list[TexHeadersRecord] = []
        self._paths: set[str] = set()
        self._source: str | None = None

    @property
    def source(self) -> str | None:
        """
        :return: Path to source file (None if not read from file)
        :rtype: str | None
        """
        return self._source

    @property
    def textures(self) -> tuple[TexHeadersRecord, ...]:
        """
        :return: Texture records
        :rtype: tuple[TexHeadersRecord, ...]
        """
        return tuple(self._textures)

    def add_texture(self, tex: TexHeadersRecord) -> None:
        """
        Adds texture record to texture index.

        :param tex: Record to add
        :type tex: TexHeadersRecord
        :raises ValueError: Path already recorded
        """
        if tex.path in self._paths:
            raise ValueError(
                f"Texture with path already exists: {tex.path}"
            )

        self._paths.add(tex.path)
        self._textures.append(tex)

    def pop_texture(self, idx: int) -> TexHeadersRecord:
        """
        Remove and return the record at the given index.

        :param idx: Index to remove
        :type idx: int
        :return: Removed record
        :rtype: TexHeadersRecord
        """
        tex = self._textures.pop(idx)
        self._paths.remove(tex.path)

        return tex

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads texture index data from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :raises TexHeadersError: Invalid or unsupported file
        :return: Texture index data
        :rtype: Self
        """
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

        output._textures = [
            TexHeadersRecord.read(stream)
            for _ in range(count_textures)
        ]

        for tex in output._textures:
            output._paths.add(tex.path)

        return output

    @classmethod
    def read_file(cls, filepath: str) -> Self:
        """
        Reads texture index data from a ``texHeaders.bin`` file.

        :param filepath: Path to ``texHeaders.bin`` file
        :type filepath: str
        :return: Texture index data
        :rtype: Self
        """
        with open(filepath, "rb") as file:
            texh = cls.read(file)

        texh._source = filepath
        return texh

    def write(self, stream: IO[bytes]) -> None:
        """
        Writes texture index data to a binary stream.

        :param stream: Target binary stream
        :type stream: IO[bytes]
        """
        binary.write_chars(stream, "0DHT")
        binary.write_ulong(stream, 1, len(self._textures))
        for tex in self._textures:
            tex.write(stream)

    def write_file(self, filepath: str) -> None:
        """
        Writes texture index data to a file.

        :param filepath: Path to target file
        :type filepath: str
        """
        with open(filepath, "wb") as file:
            self.write(file)

    @classmethod
    def from_directory(
        cls,
        dirpath: str | os.PathLike[str],
        *,
        strict: bool = False,
        ignore_dirs: str | None = r"^[\._].*$"
    ) -> Self:
        """
        Iterates the contents of a directory recursively, and creates a
        a texture index from the PAA files found within.

        :param dirpath: Path to directory
        :type dirpath: str | os.PathLike[str]
        :param strict: Stop on internal errors, defaults to False
        :type strict: bool, optional
        :param ignore_dirs: Regex pattern to ignore unwanted (eg. hidden)
            directories, defaults to ``r"^[\\._].*$"``
        :type ignore_dirs: str | None, optional
        :raises Exception: An error occured while processing a file
        :return: New texture index
        :rtype: Self
        """
        output = cls()
        ignore = (
            compile(ignore_dirs)
            if ignore_dirs is not None
            else None
        )
        for directory, subdirs, files in os.walk(dirpath):
            if ignore is not None:
                hidden = list(filter(lambda x: ignore.match(x), subdirs))
                for name in hidden:
                    subdirs.remove(name)

            for file in files:
                filepath = Path(directory, file)
                if filepath.suffix.lower() != ".paa":
                    continue

                paa = PaaFile.read_file(str(filepath))
                try:
                    output._textures.append(
                        TexHeadersRecord.from_paa(
                            filepath,
                            Path(dirpath),
                            paa
                        )
                    )
                except Exception as e:
                    if strict:
                        raise e

        return output
