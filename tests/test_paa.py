from PIL import Image

from armaio.paa import (
    PaaFile,
    PaaFormat,
    PaaAlphaFlag,
    PaaAverageColorTagg,
    PaaMaxColorTagg,
    PaaOffsetTagg,
    PaaFlagTagg
)
from armaio.paa.pillow import register_paa_codec


def test_reading() -> None:
    paa = PaaFile.read_file("tests/data/texture_co.paa")
    assert paa.format is PaaFormat.DXT1
    assert len(paa.taggs) == 4
    assert len(paa.mipmaps) == 3

    mip = paa.mipmaps[0]
    assert (mip.width, mip.height) == (16, 16)

    mip = paa.mipmaps[-1]
    assert (mip.width, mip.height) == (4, 4)

    avgc = paa.get_tagg(PaaAverageColorTagg)
    assert avgc is not None
    assert avgc.color == (175, 137, 70, 127)

    maxc = paa.get_tagg(PaaMaxColorTagg)
    assert maxc is not None
    assert maxc.color == (255, 255, 255, 255)

    flag = paa.get_tagg(PaaFlagTagg)
    assert flag is not None
    assert flag.value is PaaAlphaFlag.BINARY

    offs = paa.get_tagg(PaaOffsetTagg)
    assert offs is not None
    assert len(offs.offsets) == 16
    assert offs.offsets[0] == 128


def test_decoding() -> None:
    register_paa_codec()

    with Image.open("tests/data/texture_co.paa") as im:
        rgb = im.getpixel((0, 0))
        assert isinstance(rgb, tuple)
        assert im.mode == "RGBA"
        assert len(rgb) == 4
        assert rgb == (255, 200, 99, 255)

    with Image.open("tests/data/texture_ca.paa") as im:
        rgb = im.getpixel((0, 0))
        assert isinstance(rgb, tuple)
        assert im.mode == "RGBA"
        assert len(rgb) == 4
        assert rgb == (255, 200, 101, 127)

    with Image.open("tests/data/texture_big_ca.paa") as im:
        rgb = im.getpixel((0, 0))
        assert isinstance(rgb, tuple)
        assert im.mode == "RGBA"
        assert len(rgb) == 4
        assert rgb == (255, 200, 101, 127)

    with Image.open("tests/data/texture_nohq.paa") as im:
        rgb = im.getpixel((0, 0))
        assert isinstance(rgb, tuple)
        assert im.mode == "RGB"
        assert len(rgb) == 3
        assert rgb == (127, 127, 255)

    with Image.open("tests/data/texture_gs.paa") as im:
        rgb = im.getpixel((0, 0))
        assert isinstance(rgb, tuple)
        assert im.mode == "RGBA"
        assert len(rgb) == 4
        assert rgb == (205, 205, 205, 127)

    with Image.open("tests/data/texture_4444.paa") as im:
        rgb = im.getpixel((0, 0))
        assert isinstance(rgb, tuple)
        assert im.mode == "RGBA"
        assert len(rgb) == 4
        assert rgb == (255, 204, 102, 119)

    with Image.open("tests/data/texture_1555.paa") as im:
        rgb = im.getpixel((0, 0))
        assert isinstance(rgb, tuple)
        assert im.mode == "RGBA"
        assert len(rgb) == 4
        assert rgb == (255, 197, 99, 0)
