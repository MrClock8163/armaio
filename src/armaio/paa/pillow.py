"""
Utilities for dealing with PAA images with the Pillow library.
"""

from PIL import Image

from ._format import PaaFile


def open_paa_image(
    path: str,
    mipmap: int = 0
) -> Image.Image:
    """
    Convenience function that opens a PAA as a Pillow Image object.

    :param path: Path to PAA file
    :type path: str
    :param mipmap: Index of mipmap to open, defaults to 0
    :type mipmap: int, optional
    :return: Decoded image
    :rtype: Image.Image
    """
    paa = PaaFile.read_file(path)
    alpha = paa.is_alpha()
    data = paa.decode(mipmap)

    if not alpha:
        data = data[:, :, [0, 1, 2]]

    return Image.fromarray(data)
