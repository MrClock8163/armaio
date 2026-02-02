<h1 align="center">
<img src="https://raw.githubusercontent.com/mrclock8163/armaio/main/docs/_static/favicon.svg" alt="ArmaIO logo" width="100">
</h1><br>

[![PyPI - Version](https://img.shields.io/pypi/v/armaio)](https://pypi.org/project/armaio/)
[![Python Version](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FMrClock8163%2FArmaIO%2Frefs%2Fheads%2Fmain%2Fpyproject.toml)](https://pypi.org/project/armaio/)
[![GPLv3](https://img.shields.io/github/license/mrclock8163/armaio)](https://opensource.org/license/gpl-3-0)
[![Docs status](https://app.readthedocs.org/projects/armaio/badge/?version=latest)](https://armaio.readthedocs.io/latest/)
[![Typed](https://img.shields.io/pypi/types/armaio)](https://pypi.org/project/armaio/)

**ArmaIO** is a Python package providing utilities to read and write file
formats specific to the Arma 3 game, and its Real Virtuality 4 engine.

- **Download:** https://pypi.org/project/armaio/
- **Documentation:** https://armaio.readthedocs.io/
- **Source:** https://github.com/MrClock8163/ArmaIO
- **Bug reports:** https://github.com/MrClock8163/ArmaIO/issues

## Overview

The package supports most notable file formats used in Arma 3. Reading is
implemented for all supported formats, but writing is only available for some,
where it makes sense.

**ArmaIO** does not come with in-depth authoring utilities. The data is read
and presented in relatively thin wrapper structures, with minimal
transformation of the data structures of the files themselves. As such,
**ArmaIO** is most suited to be used as a middle layer to handle file IO in a
more complex authoring application built on top of it.

### Supported formats

- PAA
  - reading
  - processing with Pillow
  - DXT1
  - DXT5
  - ARGB8888
  - ARGB4444
  - ARGB1555
  - AI88
- RTM (plain)
  - reading
  - writing
- RTM (binarized)
  - reading
  - conversion to plain

> [!NOTE]
> The modules coming with this package were originally developed as part of
the [Arma 3 Object Builder plugin](https://github.com/MrClock8163/Arma3ObjectBuilder)
> for Blender. They are released in this standalone package to facilitate
> independent use, and easier maintenance.

## Requirements

To use the **ArmaIO** package, **Python 3.11** or higher is required.

For some operations, the package depends on NumPy. Some of the extra features
might require further dependencies. These are indicated in their respective
documentations.

## Installation

The preferred method to install **ArmaIO** is through PyPI, where both wheel
and source distributions are made available.

```shell
python -m pip install armaio
```

If not yet published changes/fixes are needed, that are only available in
source, **ArmaIO** can also be installed locally from source, without any
external tools. Once the repository is cloned to a directory, it can be
installed with pip.

```shell
git clone https://github.com/MrClock8163/ArmaIO.git
cd ArmaIO
python -m pip install .
```

## Example

```py
from armaio.paa import PaaFile
from armaio.paa.pillow import open_paa_image  # extra, requires Pillow

paa = PaaFile.read_file("texture_co.paa")
print(paa.format)

with open_paa_image("texture_co.paa") as img:
    print(img.getpixel((1, 2)))
```

## License

The **ArmaIO** package distributed under the terms of the GNU General Public
License version 3.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR  PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see the [GNU licenses](http://www.gnu.org/licenses/).

Files created using this software are not covered by this license.
