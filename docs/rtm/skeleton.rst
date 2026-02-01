Bone structure
==============

When converting the animation data from the binarized format to the
plain representation, the skeleton structure must be known. Otherwise
the absolute transformations cannot be calculated.

The conversion methods accept the skeleton data in 2 representations.

.. warning::

    In all cases, the bone names are case sensitive.

    During binarization, usually all bone names are converted to lower
    case. In that case, the skeleton data should list the bones in lower
    case as well.

Structure format
^^^^^^^^^^^^^^^^

This format specifies the skeleton structure as nested dictionaries
mapping child bones to the parents.

Each key is the name of a bone and the value is a dictionary of its
child bones, similarly further mapping to their respective child bones.

.. code-block:: python

    from armaio.rtm import BoneStructure

    skeleton: BoneStructure = {
        "root_bone": {
            "child1": {
                "child_child1": {},
                "child_child2": {
                    "child_child_child1": {}
                }
            },
            "child2": {}
        }
    }

This representation clearly shows the hierarchy of the bones.

Sequence format
^^^^^^^^^^^^^^^

The sequence format is closer to the representation used in
``model.cfg`` files. The skeleton is defined as a list of name-parent
pairs. The order of the pairs is important. A bone name should not be
referenced before it is defined in the list.

.. code-block:: python
    :caption: Correct order

    from armaio.rtm import BoneSequence, Bone

    skeleton: BoneSequence = (
        Bone("root", ""),
        Bone("child1", "root"),
        Bone("child2", "root"),
        Bone("child_child1", "child1")
    )

.. code-block:: python
    :caption: Incorrect order

    from armaio.rtm import BoneSequence, Bone

    skeleton: BoneSequence = (
        Bone("root", ""),
        Bone("child_child1", "child1"),  # child1 is referenced before it is defined
        Bone("child1", "root"),
        Bone("child2", "root")
    )

.. warning::

    Incorrect bone order will result in incorrectly converted
    transformation data.
