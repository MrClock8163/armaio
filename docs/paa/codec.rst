.. py:module:: armaio.paa.pillow
.. py:currentmodule:: armaio.paa.pillow

PAA codec for Pillow
====================

.. warning::

    This module depends on the `Pillow <https://pillow.readthedocs.io>`_
    package. It must be installed in the environment, otherwise a
    :py:class:`ModuleNotFoundError` exception will be thrown.

    Install the package manually, or install **ArmaIO** with the ``pillow``
    extra:

    .. code-block:: shell

        pip install armaio[pillow]

The `Pillow <https://pillow.readthedocs.io>`_ package is a widely used image
manipulation library for Python. It provides support for a wide range of
image formats out of the box. It also comes with a plugin system that can be
used to add support for new formats. The :py:mod:`armaio.paa.pillow` module
provides such a plugin for Arma 3 PAA files.

Normally, only the plugin registration function needs to be imported. After
the codec plugin is registered, the PAA files can be manipulated with the
`Pillow` utilities.

.. code-block:: python

    from PIL import Image
    from armaio.paa.pillow import register_paa_codec

    register_paa_codec()

    with Image.open("texture_co.paa") as im:
        im.show()

Functions
---------

.. autofunction:: register_paa_codec

Classes
-------

.. autoclass:: PaaImageFile
    :members:
