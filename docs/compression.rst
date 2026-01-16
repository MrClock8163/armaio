.. py:module:: armaio.compression
.. py:currentmodule:: armaio.compression

Compression
===========

The :py:mod:`armaio.compression` module provides functions to handle the
decompression of data blocks in certain binary formats. The module does not
currently implement the compression methods themselves.

Exceptions
----------

.. autoclass:: LzoError
.. autoclass:: LzssError

Functions
---------

.. note::

    The LZO1X decompression was implemented based on the format documentation
    found in the
    `Linux kernel documentation <https://docs.kernel.org/staging/lzo.html>`_.
    Additional inspiration was taken from the ``libavutil`` libarary
    `C implementation of LZO1X <https://github.com/FFmpeg/FFmpeg/blob/master/libavutil/lzo.c>`_
    decompression in the FFMPEG project.

    The original LZO implementations as written by Markus F.X.J. Oberhumer:

    - https://www.oberhumer.com/opensource/lzo/

.. autofunction:: lzo1x_decompress

.. note::

    The LZSS decompression was implemented based on information given on the
    `Community Wiki LZSS page <https://community.bistudio.com/wiki/Compressed_LZSS_File_Format>`_.

    Additional references:

    - `Michael Dipperstein's GitHub Site <https://michaeldipperstein.github.io/lzss.html>`_
    - `Tim Cogan's blog <https://tim.cogan.dev/lzss/>`_

    The compression method used in Arma 3 binary files is a custom flavor of
    LZSS, with the following general parameters:

    - Flag bits are grouped into bytes by eights (this allows per-byte reading
      instead of per-bit).
    - 16-bit pointers: 12-bit offset, 4-bit match length (4096 bytes sliding
      window).
    - Filler value: 0x20 (space character)

    The pointer in the file is stored in 2 bytes as ``OOOOOOOO OOOOLLLL``.
    In a somewhat confusing way, the one and a half byte offset value is
    stored as little-endian.
    This means that the 4-bits stored - together with the length - in the
    second byte must be prepended to the 8-bits in the first byte to get the
    offset.

    Since the main advantage of LZSS over LZ77 is that only those sequences are
    dictionary encoded where the pointer actually saves bytes over the literal
    copy (with a 2 byte pointer, it does not make sense to encode single bytes
    this way), the length has an implicit minimum value. To get the actual
    match length, **3 must be added** to the read length.

.. autofunction:: lzss_decompress
