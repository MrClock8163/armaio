"""
PAA coded plugin definitions for the Pillow library.
"""
from collections.abc import MutableSequence

from PIL import Image, ImageFile

from ._format import (
    PaaFile,
    PaaSwizzleTagg,
    swizzle_channels
)


def _accept(magic: bytes) -> bool:
    return (
        magic.startswith(b"\x01\xffGGAT")  # DXT1
        or magic.startswith(b"\x05\xffGGAT")  # DXT5
    )


class PaaImageFile(ImageFile.ImageFile):
    """
    Arma 3 PAA format handler.
    """
    format = "PAA"
    format_description = "Arma 3 PAA texture"

    def _open(self) -> None:
        assert self.fp is not None

        paa = PaaFile.read(self.fp)
        mip = paa.mipmaps[0]
        alpha = paa.is_alpha()
        self._size = (mip.width, mip.height)
        self._mode = "RGBA" if alpha else "RGB"

        self.tile = [
            ImageFile._Tile(
                "PAADXT",
                (0, 0) + self.size,
                0,
                (paa, alpha)
            )
        ]


class PaaDxtDecoder(ImageFile.PyDecoder):
    """
    Decoder for DXT1 and DXT5 compressed Arma 3 PAA texture files.
    """
    _pulls_fd = True

    def decode(
        self,
        buffer: bytes | Image.SupportsArrayInterface
    ) -> tuple[int, int]:
        """
        Decodes the previously read data of a DXT compressed PAA texture file.

        The method expects that the read :py:class:`~armaio.paa.PaaFile`, and
        a boolean indicating the presence of alpha data was passed as
        arguments to the instance.

        :param buffer: Binary file to be read (UNUSED)
        :type buffer: bytes | Image.SupportsArrayInterface
        :return: Bytes consumed/reading finished and error code
        :rtype: tuple[int, int]
        """
        paa: PaaFile
        alpha: bool
        paa, alpha = self.args
        mip = paa.mipmaps[0]
        channels: tuple[MutableSequence[float], ...] = mip.decompress(
            paa.format
        )

        swizzle = paa.get_tagg(PaaSwizzleTagg)
        if swizzle:
            channels = swizzle_channels(
                *channels,
                swizzle_red=swizzle.red,
                swizzle_green=swizzle.green,
                swizzle_blue=swizzle.blue,
                swizzle_alpha=swizzle.alpha
            )

        if not alpha:
            channels = channels[:3]

        raw = [
            round(255 * value)
            for color in zip(*channels)
            for value in color
        ]

        self.set_as_raw(bytes(raw))
        return -1, 0


def register_paa_codec() -> None:
    """
    Registers PAA codecs for the Pillow package.

    Extensions:
    - ``.paa``
    - ``.pac``

    Decoders:
    - ``PAADXT``: DXT1 or DXT5 compressed PAA
    """
    Image.register_decoder("PAADXT", PaaDxtDecoder)

    Image.register_open(
        PaaImageFile.format,
        PaaImageFile,
        _accept
    )

    Image.register_extensions(
        PaaImageFile.format,
        [
            ".paa",
            ".pac"  # for legacy compatibility
        ]
    )
