.. py:module:: armaio.texheaders

Texture index format
====================

The :py:mod:`armaio.texheaders` module provides support for reading and
also writing the format used by the ``texHeaders.bin`` texture index file.
The implementations are based on the information on the
`Community Wiki texHeaders.bin page <https://community.bistudio.com/wiki/texHeaders.bin_File_Format>`_.

Examples
--------

.. code-block:: python

    from armaio.texheaders import TexHeadersFile

    data = TexHeadersFile.read_file("texHeaders.bin")
    for tex in data.textures:
        print(f"tex.path ({tex.mipmaps[0].width} x {tex.mipmaps[0].height})")

Exceptions
----------

.. autoclass:: TexHeadersError

Enumerations
------------

.. autoclass:: TexHeadersTextureFormat
.. autoclass:: TexHeadersTextureSuffix

Classes
-------

.. autoclass:: TexHeadersColor
.. autoclass:: TexHeadersMipmap
.. autoclass:: TexHeadersRecord
.. autoclass:: TexHeadersFile
