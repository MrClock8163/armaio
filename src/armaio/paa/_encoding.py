from io import BytesIO
import struct
from array import array

import numpy as np
from numpy import typing as npt


def decode_argb8888(
    width: int,
    height: int,
    data: bytes | bytearray
) -> npt.NDArray[np.uint8]:
    """
    Decodes texture data encoded as 8-bit RGBA (``ARGB8888``).

    The source data is expected to be packed into one 32-bit unsigned integer
    per pixel.

    Channel layout: ``AAAAAAAA RRRRRRRR GGGGGGGG BBBBBBBB``

    :param width: Decoded texture width
    :type width: int
    :param height: Decoded texture height
    :type height: int
    :param data: Encoded binary data
    :type data: bytes | bytearray
    :return: Decoded RGBA image data
    :rtype: npt.NDArray[np.uint8]
    """
    size = width * height * 4
    output = bytearray(size)

    for i in range(0, size, 4):
        output[i + 3] = data[i + 3]
        output[i] = data[i + 2]
        output[i + 1] = data[i + 1]
        output[i + 2] = data[i]

    return np.frombuffer(
        output,
        dtype=np.uint8
    ).reshape((height, width, 4))


def decode_argb1555(
    width: int,
    height: int,
    data: bytes | bytearray
) -> npt.NDArray[np.uint8]:
    """
    Decodes texture data encoded as 5-bit RGB with binary alpha (ARGB1555).

    The source data is expected to be packed into one 16-bit unsigned integer
    per pixel.

    Channel layout: ``A RRRRR GGGGG BBBBB``

    :param width: Decoded texture width
    :type width: int
    :param height: Decoded texture height
    :type height: int
    :param data: Encoded binary data
    :type data: bytes | bytearray
    :return: Decoded RGBA image data
    :rtype: npt.NDArray[np.uint8]
    """
    output = bytearray(width * height * 4)

    for i in range(width * height):
        argb = data[i * 2] + (data[i * 2 + 1] << 8)
        pidx = i * 4
        output[pidx + 3] = (argb >> 15) * 255
        output[pidx] = round((argb >> 10 & 0b11111) / 0b11111 * 255)
        output[pidx + 1] = round((argb >> 5 & 0b11111) / 0b11111 * 255)
        output[pidx + 2] = round((argb & 0b11111) / 0b11111 * 255)

    return np.frombuffer(
        output,
        dtype=np.uint8
    ).reshape((height, width, 4))


def decode_argb4444(
    width: int,
    height: int,
    data: bytes | bytearray
) -> npt.NDArray[np.uint8]:
    """
    Decodes texture data encoded as 5-bit RGBA (ARGB4444).

    The source data is expected to be packed into one 16-bit unsigned integer
    per pixel.

    Channel layout: ``AAAA RRRR GGGG BBBB``

    :param width: Decoded texture width
    :type width: int
    :param height: Decoded texture height
    :type height: int
    :param data: Encoded binary data
    :type data: bytes | bytearray
    :return: Decoded RGBA image data
    :rtype: npt.NDArray[np.uint8]
    """
    output = bytearray(width * height * 4)

    for i in range(width * height):
        gb = data[i * 2]
        ar = data[i * 2 + 1]
        pidx = i * 4
        output[pidx + 3] = round((ar >> 4) / 0b1111 * 255)
        output[pidx] = round((ar & 0b1111) / 0b1111 * 255)
        output[pidx + 1] = round((gb >> 4) / 0b1111 * 255)
        output[pidx + 2] = round((gb & 0b1111) / 0b1111 * 255)

    return np.frombuffer(
        output,
        dtype=np.uint8
    ).reshape((height, width, 4))


def decode_ai88(
    width: int,
    height: int,
    data: bytes | bytearray
) -> npt.NDArray[np.uint8]:
    """
    Decodes texture data encoded as 8-bit grayscale (intensity) with 8-bit
    alpha (AI88).

    The source data is expected to be packed into one 16-bit unsigned integer
    per pixel.

    Channel layout: ``AAAAAAAA IIIIIIII``

    :param width: Decoded texture width
    :type width: int
    :param height: Decoded texture height
    :type height: int
    :param data: Encoded binary data
    :type data: bytes | bytearray
    :return: Decoded RGBA image data
    :rtype: npt.NDArray[np.uint8]
    """
    output = bytearray(width * height * 4)

    for i in range(width * height):
        intensity = data[i * 2]
        alpha = data[i * 2 + 1]
        pidx = i * 4
        output[pidx + 3] = alpha
        output[pidx] = intensity
        output[pidx + 1] = intensity
        output[pidx + 2] = intensity

    return np.frombuffer(
        output,
        dtype=np.uint8
    ).reshape((height, width, 4))


class DxtError(Exception):
    """Expection raised upon DXT decoding errors."""

    def __str__(self) -> str:
        return f"DXT - {super().__str__()}"


def decode_dxt1(
    width: int,
    height: int,
    data: bytes | bytearray,
) -> npt.NDArray[np.uint8]:
    """
    Decodes texture data compressed with the S3TC DXT1/BC1 algorithm.

    :param width: Texture width in pixels
    :type width: int
    :param height: Texture height in pixels
    :type height: int
    :param data: DXT1 encoded binary data
    :type data: bytes
    :raises DxtError: Could not decompress texture due to an error
    :return: Decoded RGBA image data
    :rtype: bytes
    """
    if width % 4 != 0 or height % 4 != 0:
        raise DxtError(f"Unexpected resolution: {width} x {height}")

    stream = BytesIO(data)
    output = array('f', bytearray(width * height * 4 * 4))
    struct_block = struct.Struct('<HHI')

    # Interpolation coefficients
    coef0 = 2 / 3
    coef1 = 1 / 3

    block_count_w = width // 4
    block_count_h = height // 4

    a0 = a1 = a2 = 1.0

    # Decompression of blocks from left->right, top->bottom
    v0: int
    v1: int
    table: int
    for brow in range(block_count_h):
        for bcol in range(block_count_w):
            v0, v1, table = struct_block.unpack(stream.read(8))

            # Expanding directly stored colors
            r0 = (v0 >> 11) / 31
            g0 = ((v0 >> 5) & 0x3f) / 63
            b0 = (v0 & 0x1f) / 31

            r1 = (v1 >> 11) / 31
            g1 = ((v1 >> 5) & 0x3f) / 63
            b1 = (v1 & 0x1f) / 31

            # Color interpolation
            if v0 > v1:
                r2 = coef0 * r0 + coef1 * r1
                g2 = coef0 * g0 + coef1 * g1
                b2 = coef0 * b0 + coef1 * b1

                r3 = coef1 * r0 + coef0 * r1
                g3 = coef1 * g0 + coef0 * g1
                b3 = coef1 * b0 + coef0 * b1

                a3 = 1.0
            else:
                r2 = 0.5 * (r0 + r1)
                g2 = 0.5 * (g0 + g1)
                b2 = 0.5 * (b0 + b1)

                r3 = g3 = b3 = a3 = 0.0

            # Color codes
            codes = (
                table & 0x3,
                table >> 2 & 0x3,
                table >> 4 & 0x3,
                table >> 6 & 0x3,
                table >> 8 & 0x3,
                table >> 10 & 0x3,
                table >> 12 & 0x3,
                table >> 14 & 0x3,
                table >> 16 & 0x3,
                table >> 18 & 0x3,
                table >> 20 & 0x3,
                table >> 22 & 0x3,
                table >> 24 & 0x3,
                table >> 26 & 0x3,
                table >> 28 & 0x3,
                table >> 30 & 0x3
            )
            # Color lookup
            lut = (
                (r0, g0, b0, a0),
                (r1, g1, b1, a1),
                (r2, g2, b2, a2),
                (r3, g3, b3, a3)
            )

            # Block interpretation
            # index of the starting row of the block
            bstartrow = brow * 4
            # index of the starting column of the block
            bstartcol = bcol * 4
            for row in range(4):
                # flattened index of the first pixel in the row
                current_row_col = (bstartrow + row) * width + bstartcol
                for col in range(4):
                    r, g, b, a = lut[codes[row * 4 + col]]
                    # flattened intdex of the current pixel
                    idx = (current_row_col + col) * 4
                    output[idx] = r
                    output[idx + 1] = g
                    output[idx + 2] = b
                    output[idx + 3] = a

    return (np.frombuffer(
        output,
        dtype=np.float32
    ).reshape((height, width, 4)) * 255).round().astype(np.uint8)


def decode_dxt5(
    width: int,
    height: int,
    data: bytes | bytearray,
) -> npt.NDArray[np.uint8]:
    """
    Decodes texture data compressed with the S3TC DXT5/BC3 algorithm.

    :param width: Texture width in pixels
    :type width: int
    :param height: Texture height in pixels
    :type height: int
    :param data: DXT5 encoded binary data
    :type data: bytes
    :raises DxtError: Could not decompress texture due to an error
    :return: Decoded RGBA image data
    :rtype: npt.NDArray[np.uint8]
    """
    if width % 4 != 0 or height % 4 != 0:
        raise DxtError(f"Unexpected resolution: {width} x {height}")

    stream = BytesIO(data)
    output = array('f', bytearray(width * height * 4 * 4))
    struct_block_color = struct.Struct('<HHI')
    struct_block_alpha = struct.Struct('BB')
    struct_block_atable = struct.Struct('<Q')

    # Interpolation coefficients
    acoef67 = 6 / 7
    acoef17 = 1 / 7
    acoef57 = 5 / 7
    acoef27 = 2 / 7
    acoef47 = 4 / 7
    acoef37 = 3 / 7

    acoef45 = 4 / 5
    acoef15 = 1 / 5
    acoef35 = 3 / 5
    acoef25 = 2 / 5

    coef23 = 2 / 3
    coef13 = 1 / 3

    block_count_w = width // 4
    block_count_h = height // 4

    # Decompression of blocks from left->right, top->bottom
    a0: int | float
    a1: int | float
    v0: int
    v1: int
    table: int
    atable: int
    for brow in range(block_count_h):
        for bcol in range(block_count_w):
            a0, a1, = struct_block_alpha.unpack(stream.read(2))
            atable = struct_block_atable.unpack(
                stream.read(6) + b"\x00\x00"
            )[0]
            v0, v1, table = struct_block_color.unpack(stream.read(8))

            # Expanding directly stored colors
            r0 = (v0 >> 11) / 31
            g0 = ((v0 >> 5) & 0x3f) / 63
            b0 = (v0 & 0x1f) / 31

            r1 = (v1 >> 11) / 31
            g1 = ((v1 >> 5) & 0x3f) / 63
            b1 = (v1 & 0x1f) / 31

            # Color interpolation
            if v0 > v1:
                r2 = coef23 * r0 + coef13 * r1
                g2 = coef23 * g0 + coef13 * g1
                b2 = coef23 * b0 + coef13 * b1

                r3 = coef13 * r0 + coef23 * r1
                g3 = coef13 * g0 + coef23 * g1
                b3 = coef13 * b0 + coef23 * b1
            else:
                r2 = 0.5 * (r0 + r1)
                g2 = 0.5 * (g0 + g1)
                b2 = 0.5 * (b0 + b1)
                r3 = g3 = b3 = 0.0

            # Alpha interpolation
            if a0 > a1:
                a0 /= 255
                a1 /= 255
                a2 = acoef67 * a0 + acoef17 * a1
                a3 = acoef57 * a0 + acoef27 * a1
                a4 = acoef47 * a0 + acoef37 * a1
                a5 = acoef37 * a0 + acoef47 * a1
                a6 = acoef27 * a0 + acoef57 * a1
                a7 = acoef17 * a0 + acoef67 * a1
            else:
                a0 /= 255
                a1 /= 255
                a2 = acoef45 * a0 + acoef15 * a1
                a3 = acoef35 * a0 + acoef25 * a1
                a4 = acoef25 * a0 + acoef35 * a1
                a5 = acoef15 * a0 + acoef45 * a1
                a6 = 0.0
                a7 = 1.0

            # Color code
            codes = (
                table & 0x3,
                table >> 2 & 0x3,
                table >> 4 & 0x3,
                table >> 6 & 0x3,
                table >> 8 & 0x3,
                table >> 10 & 0x3,
                table >> 12 & 0x3,
                table >> 14 & 0x3,
                table >> 16 & 0x3,
                table >> 18 & 0x3,
                table >> 20 & 0x3,
                table >> 22 & 0x3,
                table >> 24 & 0x3,
                table >> 26 & 0x3,
                table >> 28 & 0x3,
                table >> 30 & 0x3
            )
            # Alpha codes
            acodes = (
                atable & 0x7,
                atable >> 3 & 0x7,
                atable >> 6 & 0x7,
                atable >> 9 & 0x7,
                atable >> 12 & 0x7,
                atable >> 15 & 0x7,
                atable >> 18 & 0x7,
                atable >> 21 & 0x7,
                atable >> 24 & 0x7,
                atable >> 27 & 0x7,
                atable >> 30 & 0x7,
                atable >> 33 & 0x7,
                atable >> 36 & 0x7,
                atable >> 39 & 0x7,
                atable >> 42 & 0x7,
                atable >> 45 & 0x7
            )
            # Color lookup
            lut = (
                (r0, g0, b0),
                (r1, g1, b1),
                (r2, g2, b2),
                (r3, g3, b3)
            )
            # Alpha lookup
            alut = (
                a0,
                a1,
                a2,
                a3,
                a4,
                a5,
                a6,
                a7
            )

            # Block interpretation

            # index of the starting row of the block
            bstartrow = brow * 4
            # index of the starting column of the block
            bstartcol = bcol * 4
            for row in range(4):
                # flattened index of the first pixel in the row
                current_row_col = (bstartrow + row) * width + bstartcol
                for col in range(4):
                    # pixel index inside current flattened block
                    pix = row * 4 + col
                    r, g, b = lut[codes[pix]]
                    a = alut[acodes[pix]]
                    # flattened intdex of the current pixel
                    idx = (current_row_col + col) * 4
                    output[idx] = r
                    output[idx + 1] = g
                    output[idx + 2] = b
                    output[idx + 3] = a

    return (np.frombuffer(
        output,
        dtype=np.float32
    ).reshape((height, width, 4)) * 255).round().astype(np.uint8)
