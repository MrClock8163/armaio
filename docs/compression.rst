.. py:module:: armaio.compression
.. py:currentmodule:: armaio.compression

Compression
===========

The :py:mod:`armaio.compression` module provides functions to handle the decompression of data blocks in certain binary formats. The module does not currently implement the compression methods themselves.

Exceptions
----------

.. autoclass:: LzoError
.. autoclass:: DxtError

Functions
---------

Generic
^^^^^^^

.. note::

    The LZO1X decompression was implemented based on the format documentation found in the `Linux kernel documentation <https://docs.kernel.org/staging/lzo.html>`_. Additional inspiration was taken from the ``libavutil`` libarary  `C implementation of LZO1X <https://github.com/FFmpeg/FFmpeg/blob/master/libavutil/lzo.c>`_ decompression in the FFMPEG project.

    The original LZO implementations as written by Markus F.X.J. Oberhumer:

    - https://www.oberhumer.com/opensource/lzo/

.. autofunction:: lzo1x_decompress

Textures
^^^^^^^^

.. note::

    The S3TC DXT1/BC1 and DXT5/BC3 decompression algorithms are based on publically available documentation.

    - https://en.wikipedia.org/wiki/S3_Texture_Compression
    - https://www.khronos.org/opengl/wiki/S3_Texture_Compression

.. autofunction:: dxt1_decompress
.. autofunction:: dxt5_decompress
