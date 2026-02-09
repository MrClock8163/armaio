***************************************
Welcome to the **ArmaIO** documentation
***************************************

The **ArmaIO** package provides utilities to read and write file formats
specific to the Arma 3 game.

.. image:: https://img.shields.io/pypi/v/armaio
    :target: https://pypi.org/project/armaio/
    :alt: PyPI - Version

.. image:: https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FMrClock8163%2FArmaIO%2Frefs%2Fheads%2Fmain%2Fpyproject.toml
    :target: https://pypi.org/project/armaio/
    :alt: Python Version

.. image:: https://img.shields.io/github/license/mrclock8163/armaio
    :target: https://opensource.org/license/gpl-3-0
    :alt: GPLv3 License

.. image:: https://app.readthedocs.org/projects/armaio/badge/?version=latest
    :target: https://armaio.readthedocs.io/latest/
    :alt: Docs Status

.. image:: https://img.shields.io/pypi/types/armaio
    :target: https://pypi.org/project/armaio/
    :alt: Typed

Overview
========

The package supports most notable file formats used in Arma 3. Reading is
implemented for all supported formats, but writing is only available for some,
where it makes sense.

**ArmaIO** does not come with in-depth authoring utilities. The data is read
and presented in relatively thin wrapper structures, with minimal
transformation of the data structures of the files themselves. As such,
**ArmaIO** is most suited to be used as a middle layer to handle file IO in a
more complex authoring application built on top of it.

.. note::

    The modules coming with this package were originally developed as part of
    the `Arma 3 Object Builder plugin <https://github.com/MrClock8163/Arma3ObjectBuilder>`_
    for Blender. They are released in this standalone package to facilitate
    independent use, and easier maintenance.

.. toctree::
    :maxdepth: 1

    changelog

.. toctree::
    :maxdepth: 1
    :caption: External references

    Source code <https://github.com/MrClock8163/armaio>
    Published package <https://pypi.org/project/armaio/>
    Arma 3 community wiki <https://community.bistudio.com/wiki/Category:Arma_3>
    ImHex patterns <https://github.com/WerWolv/ImHex-Patterns/tree/master/patterns/a3>

.. toctree::
    :maxdepth: 1
    :caption: Core

    typing
    binary
    compression

.. toctree::
    :maxdepth: 1
    :caption: Textures

    paa/format
    paa/codec
    texheaders

.. toctree::
    :maxdepth: 1
    :caption: Animations

    rtm/plain
    rtm/binarized
    rtm/skeleton

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
