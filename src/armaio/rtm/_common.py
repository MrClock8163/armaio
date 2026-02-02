from typing import NamedTuple, TypeAlias


class RtmProperty(NamedTuple):
    """Name-value property."""
    phase: float
    """Animation phase the property is linked to."""
    name: str
    """Property name."""
    value: str
    """Property value."""


class RtmQuaternion(NamedTuple):
    """Quaternion representing a 3D rotation."""
    x: float
    y: float
    z: float
    w: float


class RtmVector(NamedTuple):
    """Vector representing a 3D position."""
    x: float
    y: float
    z: float


RtmMatrix: TypeAlias = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float]
]
"""Matrix representing 3D transformation (pre-multiply)."""


class Bone(NamedTuple):
    """Bone data."""
    name: str
    """Name of the bone."""
    parent: str
    """Name of the parent bone."""


BoneStructure: TypeAlias = dict[str, 'BoneStructure']
"""Bone hierarchy."""
BoneSequence: TypeAlias = tuple[Bone, ...]
"""Bone hierarchy as a sequence."""


def rot_loc_to_matrix(q: RtmQuaternion, v: RtmVector) -> RtmMatrix:
    """
    Converts a quaternion-vector pair to matrix representation.

    :param q: Orientation
    :type q: RtmQuaternion
    :param v: Position
    :type v: RtmVector
    :return: Transformation matrix
    :rtype: RtmMatrix
    """
    m00 = 1 - 2*q.y**2 - 2*q.z**2
    m01 = 2*q.x*q.y - 2*q.z*q.w
    m02 = 2*q.x*q.z + 2*q.y*q.w
    m10 = 2*q.x*q.y + 2*q.z*q.w
    m11 = 1 - 2*q.x**2 - 2*q.z**2
    m12 = 2*q.y*q.z - 2*q.x*q.w
    m20 = 2*q.x*q.z - 2*q.y*q.w
    m21 = 2*q.y*q.z + 2*q.x*q.w
    m22 = 1 - 2*q.x**2 - 2*q.y**2

    return (
        (m00, -m01, m02, 0.0),
        (-m10, m11, -m12, 0.0),
        (m20, -m21, m22, 0.0),
        (-v.x, v.y, -v.z, 1.0)
    )
