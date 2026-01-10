"""
Wrapper functions to simplify the reading/writing of simple binary data types
used in the file formats, as outlined on the community wiki:
https://community.bistudio.com/wiki/Generic_FileFormat_Data_Types
"""


import struct
import functools
import itertools
from typing import IO


_byte = struct.Struct("B")
_short = struct.Struct("<h")
_ushort = struct.Struct("<H")
_long = struct.Struct("<i")
_ulong = struct.Struct("<I")
_half = struct.Struct("<e")
_float = struct.Struct("<f")
_double = struct.Struct("<d")


def read_byte(stream: IO[bytes]) -> int:
    """
    Reads a single byte as an unsigned integer.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: 8-bit unsigned integer
    :rtype: int
    """
    return _byte.unpack(stream.read(1))[0]  # type: ignore[no-any-return]


def read_bytes(stream: IO[bytes], count: int = 1) -> tuple[int, ...]:
    """
    Reads multiple bytes as unsigned integers.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :param count: Number of bytes to read, defaults to 1
    :type count: int, optional
    :return: 8-bit unsigned integers
    :rtype: tuple[int, ...]
    """
    return struct.unpack(f"<{count:d}B", stream.read(count))


def read_bool(stream: IO[bytes]) -> bool:
    """
    Reads a single byte as boolean.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: Boolean value
    :rtype: bool
    """
    return read_byte(stream) != 0


def read_short(stream: IO[bytes]) -> int:
    """
    Reads a single little-endian short integer.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: 16-bit signed integer
    :rtype: int
    """
    return _short.unpack(stream.read(2))[0]  # type: ignore[no-any-return]


def read_shorts(stream: IO[bytes], count: int = 1) -> tuple[int, ...]:
    """
    Reads multiple little-endian short integers.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :param count: Number of integers to read, defaults to 1
    :type count: int, optional
    :return: 16-bit unsigned integers
    :rtype: tuple[int, ...]
    """
    return struct.unpack(f"<{count:d}h", stream.read(2 * count))


def read_ushort(stream: IO[bytes]) -> int:
    """
    Reads a single little-endian unsigned short integer.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: 16-bit unsigned integer
    :rtype: int
    """
    return _ushort.unpack(stream.read(2))[0]  # type: ignore[no-any-return]


def read_ushorts(stream: IO[bytes], count: int = 1) -> tuple[int, ...]:
    """
    Reads multiple little-endian unsigned short integers.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :param count: Number of integers to read, defaults to 1
    :type count: int, optional
    :return: 16-bit unsigned integers
    :rtype: tuple[int, ...]
    """
    return struct.unpack(f"<{count:d}H", stream.read(2 * count))


def read_long(stream: IO[bytes]) -> int:
    """
    Reads a single little-endian long integer.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: 32-bit signed integer
    :rtype: int
    """
    return _long.unpack(stream.read(4))[0]  # type: ignore[no-any-return]


def read_longs(stream: IO[bytes], count: int = 1) -> tuple[int, ...]:
    """
    Reads multiple little-endian long integers.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :param count: Number of integers to read, defaults to 1
    :type count: int, optional
    :return: 32-bit signed integers
    :rtype: tuple[int, ...]
    """
    return struct.unpack(f"<{count:d}i", stream.read(4 * count))


def read_ulong(stream: IO[bytes]) -> int:
    """
    Reads a single little-endian unsigned long integer.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: 32-bit unsigned integer
    :rtype: int
    """
    return _ulong.unpack(stream.read(4))[0]  # type: ignore[no-any-return]


def read_ulongs(stream: IO[bytes], count: int = 1) -> tuple[int, ...]:
    """
    Reads multiple little-endian unsigned long integers.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :param count: Number of integers to read, defaults to 1
    :type count: int, optional
    :return: 32-bit unsigned integers
    :rtype: tuple[int, ...]
    """
    return struct.unpack(f"<{count:d}I", stream.read(4 * count))


def read_compressed_uint(stream: IO[bytes]) -> int:
    """
    Reads a little-endian compressed unsigned integer.

    Compressed integers take up an arbitrary number of bytes. In each byte,
    the high bit signals if the next byte has to be read.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: 7-bit encoded compressed unsigned integer
    :rtype: int
    """
    output = read_byte(stream)
    extra = output

    byte_idx = 1
    while extra & 0x80:
        extra = read_byte(stream)
        output += (extra - 1) << (byte_idx * 7)
        byte_idx += 1

    return output


def read_half(stream: IO[bytes]) -> float:
    """
    Reads a single little-endian half-precision float.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: 16-bit float
    :rtype: float
    """
    return _half.unpack(stream.read(2))[0]  # type: ignore[no-any-return]


def read_halfs(stream: IO[bytes], count: int = 1) -> tuple[float, ...]:
    """
    Reads multiple little-endian half-precision floats.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :param count: Number of floats to read, defaults to 1
    :type count: int, optional
    :return: 16-bit floats
    :rtype: tuple[float, ...]
    """
    return struct.unpack(f"<{count:d}e", stream.read(2 * count))


def read_float(stream: IO[bytes]) -> float:
    """
    Reads a single little-endian single-precision float.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: 32-bit float
    :rtype: float
    """
    return _float.unpack(stream.read(4))[0]  # type: ignore[no-any-return]


def read_floats(stream: IO[bytes], count: int = 1) -> tuple[float, ...]:
    """
    Reads multiple little-endian single-precision floats.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :param count: Number of floats to read, defaults to 1
    :type count: int, optional
    :return: 32-bit floats
    :rtype: tuple[float, ...]
    """
    return struct.unpack(f"<{count:d}f", stream.read(4 * count))


def read_double(stream: IO[bytes]) -> float:
    """
    Reads a single little-endian double-precision float.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: 64-bit float
    :rtype: float
    """
    return _double.unpack(stream.read(8))[0]  # type: ignore[no-any-return]


def read_doubles(stream: IO[bytes], count: int = 1) -> tuple[float, ...]:
    """
    Reads multiple little-endian double-precision floats.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :param count: Number of floats to read, defaults to 1
    :type count: int, optional
    :return: 64-bit floats
    :rtype: tuple[float, ...]
    """
    return struct.unpack(f"<{count:d}d", stream.read(8 * count))


# In theory all strings in BI files should be strictly ASCII,
# but on the off chance that a corrupt character is present, the method would
# fail. Therefore using UTF-8 decoding is more robust, and gives the same
# result for valid ASCII values.


def read_char(stream: IO[bytes], count: int = 1) -> str:
    """
    Reads a sequence of ASCII characters.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :param count: Number of characters to read, defaults to 1
    :type count: int, optional
    :return: String of ASCII characters
    :rtype: str
    """
    chars: bytes = struct.unpack(f"{count:d}s", stream.read(count))[0]
    return chars.decode("utf8", errors="replace")


# https://stackoverflow.com/a/32775270
def read_asciiz(stream: IO[bytes]) -> str:
    """
    Reads a NULL-terminated ASCII string.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :return: ASCII string
    :rtype: str
    """
    iterbytes = iter(functools.partial(stream.read, 1), b"")
    return b"".join(
        itertools.takewhile(b"\x00".__ne__, iterbytes)
    ).decode("utf8", errors="replace")


def read_asciiz_field(stream: IO[bytes], field: int) -> str:
    """
    Reads a NULL-terminated ASCII string NULL padded to field length.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :param field: Field length
    :type field: int
    :raises EOFError: EOF was encountered in given length
    :raises ValueError: Terminator NULL was not found in field
    :return: ASCII string
    :rtype: str
    """
    data = stream.read(field)
    if len(data) < field:
        raise EOFError("ASCIIZ field ran into unexpected EOF")

    parts = data.split(b"\x00")
    if len(parts) < 2:
        raise ValueError("ASCIIZ field length overflow")

    return parts[0].decode("utf8", errors="replace")


def read_lascii(stream: IO[bytes]) -> str:
    """
    Reads a length-prefixed ASCII string.

    The string can be at most 255 characters long.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :raises EOFError: EOF was encountered in expected length
    :return: ASCII string
    :rtype: str
    """
    length = read_byte(stream)
    value = stream.read(length)
    if len(value) != length:
        raise EOFError("LASCII string ran into unexpected EOF")

    return value.decode("utf8", errors="replace")


def write_byte(stream: IO[bytes], *args: int) -> None:
    """
    Writes integers as bytes.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param args: 8-bit unsigned integers
    :type args: int
    """
    stream.write(struct.pack(f"{len(args):d}B", *args))


def write_bool(stream: IO[bytes], value: bool) -> None:
    """
    Writes a boolean as a byte.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param value: Boolean value
    :type value: bool
    """
    write_byte(stream, value)


def write_short(stream: IO[bytes], *args: int) -> None:
    """
    Writes little-endian short integers.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param args: 16-bit integers
    :type args: int
    """
    stream.write(struct.pack(f"<{len(args):d}h", *args))


def write_ushort(stream: IO[bytes], *args: int) -> None:
    """
    Writes little-endian unsigned short integers.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param args: 16-bit unsigned integers
    :type args: int
    """
    stream.write(struct.pack(f"<{len(args):d}H", *args))


def write_long(stream: IO[bytes], *args: int) -> None:
    """
    Writes little-endian long integers.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param args: 32-bit integers
    :type args: int
    """
    stream.write(struct.pack(f"<{len(args):d}i", *args))


def write_ulong(stream: IO[bytes], *args: int) -> None:
    """
    Writes little-endian unsigned long integers.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param args: 32-bit unsigned integers
    :type args: int
    """
    stream.write(struct.pack(f"<{len(args):d}I", *args))


def write_compressed_uint(stream: IO[bytes], value: int) -> None:
    """
    Writes a little-endian compressed unsigned integer.

    Compressed integers take up an arbitrary number of bytes. In each byte,
    the high bit signals if the next byte has to be read.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param value: Unsigned integer
    :type value: int
    """
    temp = value
    while True:
        if temp < 128:
            write_byte(stream, temp)
            break

        write_byte(stream, (temp & 127) + 128)
        temp = temp >> 7


def write_half(stream: IO[bytes], *args: float) -> None:
    """
    Writes little-endian half-precision floats.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param args: 16-bit floats
    :type args: float
    """
    stream.write(struct.pack(f"<{len(args):d}e", *args))


def write_float(stream: IO[bytes], *args: float) -> None:
    """
    Writes little-endian single-precision floats.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param args: 32-bit floats
    :type args: float
    """
    stream.write(struct.pack(f"<{len(args):d}f", *args))


def write_double(stream: IO[bytes], *args: float) -> None:
    """
    Writes little-endian double-precision floats.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param args: 64-bit floats
    :type args: float
    """
    stream.write(struct.pack(f"<{len(args):d}d", *args))


def write_chars(stream: IO[bytes], values: str) -> None:
    """
    Writes a sequence of ASCII characters.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param values: ASCII string
    :type values: str
    """
    stream.write(struct.pack(f"<{len(values):d}s", values.encode('ascii')))


def write_asciiz(stream: IO[bytes], value: str) -> None:
    """
    Writes a NULL-terminated ASCII string.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param value: ASCII string
    :type value: str
    """
    stream.write(struct.pack(f"<{len(value) + 1:d}s", value.encode('ascii')))


def write_asciiz_field(stream: IO[bytes], value: str, field: int) -> None:
    """
    Writes a NULL-terminated ASCII string to a NULL paddded field.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param value: ASCII string
    :type value: str
    :param field: Field length
    :type field: int
    :raises ValueError: String with NULL-terminator does not fit into field
    """
    if (len(value) + 1) > field:
        raise ValueError(
            f"ASCIIZ value is longer ({len(value):d} + 1) "
            f"than field length ({field:d})"
        )

    stream.write(struct.pack(f"<{field:d}s", value.encode('ascii')))


def write_lascii(stream: IO[bytes], value: str) -> None:
    """
    Writes length-prefixed ASCII string.

    The string can be at most 255 characters.

    :param stream: Target binary stream
    :type stream: IO[bytes]
    :param value: ASCII string
    :type value: str
    :raises ValueError: String is longer than 255 characters
    """
    length = len(value)
    if length > 255:
        raise ValueError("LASCII string cannot be longer than 255 characters")

    stream.write(struct.pack(f'B{length:d}s', length, value.encode('ascii')))
