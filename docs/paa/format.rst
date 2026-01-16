.. py:module:: armaio.paa
.. py:currentmodule:: armaio.paa

PAA format
==========

The :py:mod:`armaio.paa` package provides facilities for reading the PAA
texture format. The implementation are based on the information on the
`Community Wiki PAA page <https://community.bistudio.com/wiki/PAA_File_Format>`_

The module supports all PAA types available in the **TexView** application.

Examples
--------

Decoding a mipmap
^^^^^^^^^^^^^^^^^

.. code-block:: python

    from armaio.paa import PaaFile, PaaSwizzleTagg, swizzle_channels

    paa = PaaFile.read("texture_co.paa")
    mip0 = paa.mipmaps[0]
    rgba = mip0.decode(paa.format)
    swizzle = paa.get_tagg(PaaSwizzleTagg)
    if swizzle:
        rgba = swizzle_channels(
            rgba,
            swizzle_red=swizzle.red
            swizzle_green=swizzle.green
            swizzle_blue=swizzle.blue
            swizzle_alpha=swizzle.alpha
        )

Using convenience function
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from armaio.paa import PaaFile

    paa = PaaFile.read("texture_co.paa")
    rgba = paa.decode()

Functions
---------

Decoding
^^^^^^^^

.. note::

    The implementations of the S3TC DXT1/BC1 and DXT5/BC3 decoding algorithms
    are based on publically available documentation:

    - `Wikipedia <https://en.wikipedia.org/wiki/S3_Texture_Compression>`_
    - `OpenGL Wiki <https://www.khronos.org/opengl/wiki/S3_Texture_Compression>`_

.. autofunction:: decode_dxt1
.. autofunction:: decode_dxt5

.. note::

    The implementations of the bit packed decodings are based on the
    `Community Wiki <https://community.bistudio.com/wiki/PAA_File_Format>`_

.. autofunction:: decode_argb8888
.. autofunction:: decode_argb1555
.. autofunction:: decode_argb4444
.. autofunction:: decode_ai88

Utilities
^^^^^^^^^

.. autofunction:: swizzle_channels

Exceptions
----------

.. autoclass:: PaaError
.. autoclass:: DxtError

Enumerations
------------

.. autoclass:: PaaFormat
    :members:
    :member-order: bysource
.. autoclass:: PaaAlphaFlag
    :members:
    :member-order: bysource
.. autoclass:: PaaSwizzle
    :members:
    :member-order: bysource

Classes
-------

.. autoclass:: PaaTagg
.. autoclass:: PaaUnknownTagg
    :members:
    :member-order: groupwise
.. autoclass:: PaaAverageColorTagg
    :members:
    :member-order: groupwise
.. autoclass:: PaaMaxColorTagg
    :members:
    :member-order: groupwise
.. autoclass:: PaaFlagTagg
    :members:
    :member-order: groupwise
.. autoclass:: PaaSwizzleTagg
    :members:
    :member-order: groupwise
.. autoclass:: PaaOffsetTagg
    :members:
    :member-order: groupwise
.. autoclass:: PaaMipmap
    :members:
    :member-order: groupwise
.. autoclass:: PaaFile
    :members:
    :member-order: groupwise