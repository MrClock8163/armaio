.. py:currentmodule:: armaio.rtm

BMTR format (binarized RTM)
===========================

The :py:mod:`armaio.rtm` module provides utilites for reading the binarized RTM
animation format. The implementations are based on the
`Community Wiki binarized RTM page <https://community.bistudio.com/wiki/Rtm_Binarised_File_Format>`_
and further research.

For "binarized" RTM files, the module only supports reading. Writing is only
supported through conversion to the "plain" representation.

.. warning::

    While both the "plain" and "binarized" RTM formats use the ``.rtm``
    extension, the actual file format is completely different, and not
    interchangeable.

    In contrast to "plain" files, the BMTR format uses optional compression
    in some data blocks, and the transformation data itself is stored as
    relative quaternion-vector pairs, instead of absolute matrices.

Examples
--------

Reading
^^^^^^^

.. code-block:: python

    from armaio.rtm import BmtrFile

    bmtr = BmtrFile.read_file("animation_binarized.rtm")
    print(bmtr.motion)


Converting
^^^^^^^^^^

.. code-block:: python
    
    from armaio.rtm import RtmFile, BmtrFile, BoneStructure

    bmtr = BmtrFile.read_file("animation_binarized.rtm")
    skeleton: BoneStructure = {
        "pelvis": {
            "torso": {
                "leftarm": {},
                "rightarm": {}
            }
        }
    }

    rtm = RtmFile.from_binarized(bmtr, skeleton)
    print(rtm.motion)

Exceptions
----------

.. autoclass:: BmtrError


Classes
-------

.. autoclass:: BmtrFrame
.. autoclass:: BmtrFile
