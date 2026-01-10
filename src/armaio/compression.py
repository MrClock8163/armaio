"""Algorithms for handling compressed data blocks in Arma 3 file formats."""


import struct
from typing import IO, BinaryIO
from io import BytesIO


class LzoError(Exception):
    """Exception raised upon LZO decompression errors."""

    def __str__(self) -> str:
        return f"LZO - {super().__str__()}"


def lzo1x_decompress(
    data: bytes | bytearray | IO[bytes] | BinaryIO,
    expected_length: int
) -> tuple[int, bytes]:
    """
    Decompresses data compressed with the LZO1X algorithm.

    :param data: Source binary data
    :type data: bytes | bytearray | IO[bytes] | BinaryIO
    :param expected: Expected decompressed length
    :type expected: int
    :raises LzoError: Could not decompress data due to an error
    :return: Number of consumed bytes and the decompressed data
    :rtype: tuple[int, bytes]
    """
    stream: IO[bytes]
    if isinstance(data, (bytes, bytearray)):
        stream = BytesIO(data)
    else:
        stream = data

    state = 0
    start = stream.tell()
    output = bytearray()

    struct_le16 = struct.Struct('<H')

    def check_free_space(length: int) -> None:
        free_space = expected_length - len(output)
        if free_space < length:
            raise LzoError(
                f"Output overrun (free buffer: {free_space:d}, "
                f"match length: {length:d})"
            )

    def copy_match(
        distance: int,
        length: int
    ) -> None:
        check_free_space(length)

        # It is valid to have length that is longer than the back pointer
        # distance, which creates a repeating pattern, copying the same bytes
        # that were copied in this same command. For this reason, we cannot
        # simply take a slice of the output at the given point with the given
        # length, as some of the bytes might not yet be there. We have to copy
        # in chunks with size of the backpointer distance.
        start = len(output) - distance
        # copy as many whole chunks as possible
        output.extend(output[start:] * (length // distance))
        # copy remainder
        output.extend(output[start:(start + (length % distance))])

    def get_length(
        x: int,
        mask: int
    ) -> int:
        length = x & mask
        if not length:
            while True:
                x = stream.read(1)[0]
                if x:
                    break

                length += 255
            length += mask + x
        return length

    # First byte is handled separately, as the output buffer is empty at
    # this point.
    x = stream.read(1)[0]
    if x > 17:
        length = x - 17
        check_free_space(length)
        output.extend(stream.read(length))
        state = min(4, length)
        x = stream.read(1)[0]

    while True:
        if x <= 15:
            if not state:
                length = 3 + get_length(x, 15)
                check_free_space(length)
                output.extend(stream.read(length))
                state = 4
            elif state < 4:
                length = 2
                state = x & 3
                distance = (stream.read(1)[0] << 2) + (x >> 2) + 1
                copy_match(distance, length)
                check_free_space(state)
                output.extend(stream.read(state))
            elif state == 4:
                length = 3
                state = x & 3
                distance = (stream.read(1)[0] << 2) + (x >> 2) + 2049
                copy_match(distance, length)
                check_free_space(state)
                output.extend(stream.read(state))
        elif x > 127:
            state = x & 3
            length = 5 + ((x >> 5) & 3)
            distance = (stream.read(1)[0] << 3) + ((x >> 2) & 7) + 1
            copy_match(distance, length)
            check_free_space(state)
            output.extend(stream.read(state))
        elif x > 63:
            state = x & 3
            length = 3 + ((x >> 5) & 1)
            distance = (stream.read(1)[0] << 3) + ((x >> 2) & 7) + 1
            copy_match(distance, length)
            check_free_space(state)
            output.extend(stream.read(state))
        elif x > 31:
            length = 2 + get_length(x, 31)
            extra = struct_le16.unpack(stream.read(2))[0]
            distance = (extra >> 2) + 1
            state = extra & 3
            copy_match(distance, length)
            check_free_space(state)
            output.extend(stream.read(state))
        else:
            length = 2 + get_length(x, 7)
            extra = struct_le16.unpack(stream.read(2))[0]
            distance = 16384 + ((x & 8) << 11) + (extra >> 2)
            state = extra & 3
            if distance == 16384:
                if length != 3:
                    raise LzoError(
                        "Invalid End Of Stream "
                        f"(expected match length: 3, got: {length:d})"
                    )
                # End of Stream reached
                break

            copy_match(distance, length)
            check_free_space(state)
            output.extend(stream.read(state))

        x = stream.read(1)[0]

    if expected_length - len(output):
        raise LzoError(
            "Stream provided shorter output than expected "
            f"(expected: {expected_length:d}, got: {len(output)})"
        )

    return stream.tell() - start, bytes(output)


class LzssError(Exception):
    """Exception raised upon LZSS decompression errors."""

    def __str__(self) -> str:
        return f"LZSS - {super().__str__()}"


def lzss_decompress(
    data: bytes | bytearray | IO[bytes] | BinaryIO,
    expected_length: int,
    *,
    signed_checksum: bool = False
) -> tuple[int, bytes]:
    """
    Decompress data compressed with the LZSS algorithm.

    :param data: Source binary data
    :type data: bytes | bytearray | IO[bytes] | BinaryIO
    :param expected_length: Expected decompressed length
    :type expected_length: int
    :param signed_checksum: Use signed checksum instead of unsigned, defaults
        to False
    :type signed_checksum: bool, optional
    :raises LzssError: Could not decompress data due to an error
    :return: Number of consumed bytes and the decompressed data
    :rtype: tuple[int, bytes]
    """
    stream: IO[bytes]
    if isinstance(data, (bytes, bytearray)):
        stream = BytesIO(data)
    else:
        stream = data

    start = stream.tell()
    output = bytearray()

    def read_pointer() -> tuple[int, int]:
        offset, length = stream.read(2)
        offset += (length & 0xf0) << 4
        length = (length & 0x0f) + 3  # minimum length is 3

        return offset, length

    while len(output) < expected_length:
        flag = stream.read(1)[0]
        for bit in range(8):
            if len(output) >= expected_length:
                break

            if flag & 2**bit:
                output.extend(stream.read(1))
                continue

            offset, length = read_pointer()
            start = len(output) - offset
            # filler 0x20 when start is before the buffer beginning
            output.extend(-start * b"\x20")
            # copy as many whole chunks as possible
            output.extend(output[start:] * (length // offset))
            # copy remainder
            output.extend(output[start:(start + (length % offset))])

    if signed_checksum:
        checksum_read: int = struct.unpack("<i", stream.read(4))[0]
        checksum_unpacked = sum(
            map(
                lambda x: x - (x >> 7 << 8),  # signed sum
                output
            )
        )
        # just to be sure
        checksum_unpacked &= 0xffffffff
        checksum_unpacked -= (checksum_unpacked >> 31 << 32)
    else:
        checksum_read = struct.unpack("<I", stream.read(4))[0]
        checksum_unpacked = sum(output) & 0xffffffff

    if checksum_unpacked != checksum_read:
        raise LzssError(
            f"Checksum mismatch: read {checksum_read:d}, "
            f"calculated {checksum_unpacked:d}"
        )

    return stream.tell() - start, bytes(output)
