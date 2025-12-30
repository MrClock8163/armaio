.. py:module:: armaio.binary
.. py:currentmodule:: armaio.binary

Core binary IO
==============

The :py:mod:`armaio.binary` module provides utility functions for reading and writing the basic data types used in Arma 3 file formats as outlined on the `community wiki <https://community.bistudio.com/wiki/Generic_FileFormat_Data_Types>`_.

Examples
--------

The following examples give a simple demonstration about the usage of the function in the module.

Writing
^^^^^^^

.. code-block:: python

    from armaio import binary as a3io

    with open("file.bin", "wb") as file:
        a3io.write_chars(file, "A3IO")
        version_major = 2
        version_minor = 1
        a3io.write_ushort(file, version_major, version_minor)
        count = 10
        a3io.write_compressed_uint(file, count)
        for i in range(count):
            a3io.write_ulong(file, i)

Reading
^^^^^^^

.. code-block:: python

    from armaio import binary as a3io

    with open("file.bin", "rb") as file:
        signature = a3io.read_char(file)
        version_major, version_minor = a3io.read_ushorts(file, 2)
        count = a3io.read_compressed_uint(file)
        data = []
        for i in range(count):
            data.append(a3io.read_ulong(file))

Functions
---------

String reading
^^^^^^^^^^^^^^

.. autofunction:: read_asciiz
.. autofunction:: read_asciiz_field
.. autofunction:: read_lascii
.. autofunction:: read_char

String writing
^^^^^^^^^^^^^^

.. autofunction:: write_asciiz
.. autofunction:: write_asciiz_field
.. autofunction:: write_lascii
.. autofunction:: write_chars

Integer reading
^^^^^^^^^^^^^^^

.. autofunction:: read_bool
.. autofunction:: read_byte
.. autofunction:: read_bytes
.. autofunction:: read_short
.. autofunction:: read_shorts
.. autofunction:: read_ushort
.. autofunction:: read_ushorts
.. autofunction:: read_long
.. autofunction:: read_longs
.. autofunction:: read_ulong
.. autofunction:: read_ulongs
.. autofunction:: read_compressed_uint

Integer writing
^^^^^^^^^^^^^^^

.. autofunction:: write_bool
.. autofunction:: write_byte
.. autofunction:: write_short
.. autofunction:: write_ushort
.. autofunction:: write_long
.. autofunction:: write_ulong
.. autofunction:: write_compressed_uint


Float reading
^^^^^^^^^^^^^

.. autofunction:: read_half
.. autofunction:: read_halfs
.. autofunction:: read_float
.. autofunction:: read_floats
.. autofunction:: read_double
.. autofunction:: read_doubles

Float writing
^^^^^^^^^^^^^

.. autofunction:: write_half
.. autofunction:: write_float
.. autofunction:: write_double
