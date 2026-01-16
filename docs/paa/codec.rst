.. py:module:: armaio.paa.pillow
.. py:currentmodule:: armaio.paa.pillow

PAA utilities for Pillow
========================

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
image formats out of the box. The :py:mod:`armaio.paa.pillow` module
provides utilities to deal with Arma 3 PAA files.

.. code-block:: python

    from PIL import Image
    from armaio.paa.pillow import open_paa_image

    with open_paa_image("texture_co.paa") as im:
        im.show()

Functions
---------

.. autofunction:: open_paa_image
