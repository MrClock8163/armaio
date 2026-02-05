from io import BytesIO

from armaio.texheaders import (
    TexHeadersFile,
    TexHeadersTextureFormat,
    TexHeadersTextureSuffix,
    TexHeadersRecord,
    TexHeadersMipmap,
    TexHeadersColor
)


def test_reading() -> None:
    data = TexHeadersFile.read_file("tests/data/texHeaders.bin")

    assert len(data.textures) == 7

    sizes = (16, 16, 256, 16, 16, 16, 16)
    suffixes = (
        TexHeadersTextureSuffix.DIFFUSE,
        TexHeadersTextureSuffix.DIFFUSE,
        TexHeadersTextureSuffix.DIFFUSE,
        TexHeadersTextureSuffix.DIFFUSE,
        TexHeadersTextureSuffix.DIFFUSE,
        TexHeadersTextureSuffix.DIFFUSE,
        TexHeadersTextureSuffix.NORMAL
    )
    encodings = (
        TexHeadersTextureFormat.ARGB1555,
        TexHeadersTextureFormat.ARGB4444,
        TexHeadersTextureFormat.DXT5,
        TexHeadersTextureFormat.DXT5,
        TexHeadersTextureFormat.DXT1,
        TexHeadersTextureFormat.GRAY,
        TexHeadersTextureFormat.DXT5
    )

    for tex, size, suffix, encoding in zip(
        data.textures,
        sizes,
        suffixes,
        encodings
    ):
        assert tex.mipmaps[0].width == tex.mipmaps[0].height == size
        assert tex.suffix is suffix
        assert tex.format is encoding
        assert tex.is_paa

    tex0 = data.textures[0]
    assert tex0.maxcolor_defined
    assert tex0.color_average == (255, 200, 100, 127)
    assert tex0.color_max == (255, 255, 255, 255)
    assert tex0.filesize == 286


def test_writing() -> None:
    texh = TexHeadersFile()

    mip0 = TexHeadersMipmap(
        256,
        256,
        TexHeadersTextureFormat.DXT5,
        1234
    )
    tex0 = TexHeadersRecord(
        TexHeadersColor(1.0, 0.0, 0.0, 1.0),
        TexHeadersColor(255, 0, 0, 255),
        TexHeadersColor(255, 255, 255, 255),
        True,
        True,
        False,
        True,
        TexHeadersTextureFormat.DXT5,
        True,
        "texture_ca.paa",
        TexHeadersTextureSuffix.MACRO,
        (mip0,),
        5678
    )
    texh.add_texture(tex0)

    with BytesIO() as stream:
        texh.write(stream)
