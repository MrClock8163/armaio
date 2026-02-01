.. py:module:: armaio.rtm
.. py:currentmodule:: armaio.rtm

RTM format
==========

The :py:mod:`armaio.rtm` module provides utilites for reading and writing the
RTM animation format. The implementations are based on the
`Community Wiki RTM page <https://community.bistudio.com/wiki/Rtm_(Animation)_File_Format>`_
and further research.

For "plain" RTM files, the module supports both reading and writing.

Examples
--------

Reading
^^^^^^^

.. code-block:: python

    from armaio.rtm import RtmFile

    rtm = RtmFile.read_file("animation.rtm")
    print(rtm.motion)

Writing
^^^^^^^

.. code-block:: python

    from armaio.rtm import RtmFile, RtmFrame

    rtm = RtmFile()
    rtm.add_property(0.1, "StepSound", "")
    bones = ("bone1", "bone2")
    frame0 = RtmFrame(0.0, bones)
    frame1 = RtmFrame(1.0, bones)

    mat = (
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (1.0, 2.0, 3.0, 1.0)
    )
    frame1.set_transform(
        "bone1",
        mat
    )

    rtm.add_frame(frame0)
    rtm.add_frame(frame1)

    rtm.write_file("animation.rtm")

Exceptions
----------

.. autoclass:: RtmError

Classes
-------

.. autoclass:: RtmProperty
.. autodata:: RtmMatrix
.. autoclass:: RtmVector
.. autoclass:: RtmQuaternion
.. autoclass:: Bone
.. autodata:: BoneStructure
.. autodata:: BoneSequence

.. autoclass:: RtmFrame
.. autoclass:: RtmFile
