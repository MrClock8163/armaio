.. py:module:: armaio.paa
.. py:currentmodule:: armaio.paa

PAA format
==========

The :py:mod:`armaio.paa` provides facilities for reading the PAA texture format.

Examples
--------

.. code-block:: python

    from armaio.paa import PaaFile, PaaSwizzleTagg, swizzle_channels

    paa = PaaFile.read("texture_co.paa")
    mip0 = paa.mipmaps[0]
    red, green, blue, alpha = mip0.decompress(paa.format)
    swizzle = paa.get_tagg(PaaSwizzleTagg)
    if swizzle:
        red, green, blue, alpha = swizzle_channels(
            red,
            green,
            blue,
            alpha,
            swizzle_red=swizzle.red
            swizzle_green=swizzle.green
            swizzle_blue=swizzle.blue
            swizzle_alpha=swizzle.alpha
        )

Functions
---------

.. autofunction:: reverse_row_order
.. autofunction:: swizzle_channels

Exceptions
----------

.. autoclass:: PaaError

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