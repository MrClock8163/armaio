"""
PAA codec plugin definitions for the Pillow library.
"""

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
        or magic.startswith(b"\x44\x44GGAT")  # RGBA4444
        or magic.startswith(b"\x55\x15GGAT")  # RGBA5551
        or magic.startswith(b"\x88\x88GGAT")  # RGBA8888
        or magic.startswith(b"\x80\x80GGAT")  # GRAY
    )


def _strip_alpha(
    width: int,
    height: int,
    data: bytes | bytearray
) -> bytes:
    output = bytearray()

    for i in range(0, width * height * 4, 4):
        output.extend(data[i:(i+3)])

    return bytes(output)


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
                "PAA",
                (0, 0) + self.size,
                0,
                (paa, alpha)
            )
        ]


class _PaaDecoder(ImageFile.PyDecoder):
    """
    Decoder for Arma 3 PAA texture files.
    """
    _pulls_fd = True

    def decode(
        self,
        buffer: bytes | Image.SupportsArrayInterface
    ) -> tuple[int, int]:
        """
        Decodes the previously read data of a PAA texture file supporting
        various pixel formats.

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
        data = mip.decode(paa.format)

        swizzle = paa.get_tagg(PaaSwizzleTagg)
        if swizzle:
            data = swizzle_channels(
                data,
                swizzle_red=swizzle.red,
                swizzle_green=swizzle.green,
                swizzle_blue=swizzle.blue,
                swizzle_alpha=swizzle.alpha
            )

        if not alpha:
            data = _strip_alpha(mip.width, mip.height, data)

        self.set_as_raw(data)
        return -1, 0


def register_paa_codec() -> None:
    """
    Registers PAA codec for the Pillow package.

    Extensions:

    - ``.paa``
    - ``.pac``

    Decoders:

    - ``PAA``
    """
    Image.register_decoder("PAA", _PaaDecoder)

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
