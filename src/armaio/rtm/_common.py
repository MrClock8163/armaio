from typing import NamedTuple, TypeAlias


class RtmProperty(NamedTuple):
    phase: float
    name: str
    value: str


class RtmQuaternion(NamedTuple):
    x: float
    y: float
    z: float
    w: float


class RtmVector(NamedTuple):
    x: float
    y: float
    z: float


RtmMatrix: TypeAlias = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float]
]


BoneStructure = dict[str, 'BoneStructure']


class Bone(NamedTuple):
    name: str
    parent: str
