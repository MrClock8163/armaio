from io import BytesIO

from pytest import approx, raises

from armaio import binary


def test_integers() -> None:
    with BytesIO() as stream:
        binary.write_byte(stream, 1, 2, 3)
        binary.write_bool(stream, False)
        binary.write_bool(stream, True)
        binary.write_short(stream, 32000, 1, 32001)
        binary.write_ushort(stream, 64000, 1, 64001)
        binary.write_long(stream, 2_000_000_000, 1, 2_000_000_001)
        binary.write_ulong(stream, 4_000_000_000, 1, 4_000_000_001)
        binary.write_compressed_uint(stream, 65536)
        binary.write_half(stream, 0.5, 0.5, 0.5)
        binary.write_float(stream, 0.5, 0.5, 0.5)
        binary.write_double(stream, 0.5, 0.5, 0.5)

        stream.seek(0)
        assert binary.read_byte(stream) == 1
        assert binary.read_bytes(stream, 2) == (2, 3)
        assert binary.read_bool(stream) is False
        assert binary.read_bool(stream) is True
        assert binary.read_short(stream) == 32000
        assert binary.read_shorts(stream, 2) == (1, 32001)
        assert binary.read_ushort(stream) == 64000
        assert binary.read_ushorts(stream, 2) == (1, 64001)
        assert binary.read_long(stream) == 2_000_000_000
        assert binary.read_longs(stream, 2) == (1, 2_000_000_001)
        assert binary.read_ulong(stream) == 4_000_000_000
        assert binary.read_ulongs(stream, 2) == (1, 4_000_000_001)
        assert binary.read_compressed_uint(stream) == 65536
        assert binary.read_half(stream) == approx(0.5)
        assert binary.read_halfs(stream, 2) == approx((0.5, 0.5))
        assert binary.read_float(stream) == approx(0.5)
        assert binary.read_floats(stream, 2) == approx((0.5, 0.5))
        assert binary.read_double(stream) == approx(0.5)
        assert binary.read_doubles(stream, 2) == approx((0.5, 0.5))


def test_strings() -> None:
    with BytesIO() as stream:
        binary.write_chars(stream, "test")
        binary.write_asciiz(stream, "test")
        binary.write_asciiz_field(stream, "test", 20)
        binary.write_lascii(stream, "test")

        stream.seek(0)
        assert binary.read_char(stream, 4) == "test"
        assert binary.read_asciiz(stream) == "test"
        assert binary.read_asciiz_field(stream, 20) == "test"
        assert binary.read_lascii(stream) == "test"

    with BytesIO() as stream:
        with raises(ValueError):
            binary.write_asciiz_field(stream, "test", 4)

        with raises(ValueError):
            binary.write_lascii(stream, "a" * 256)

    with BytesIO() as stream:
        with raises(EOFError):
            binary.read_asciiz_field(stream, 1)

    with BytesIO(b"test") as stream:
        with raises(ValueError):
            binary.read_asciiz_field(stream, 4)

    with BytesIO(b"\x05test") as stream:
        with raises(EOFError):
            binary.read_lascii(stream)
