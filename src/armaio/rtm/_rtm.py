from typing import Self, IO, cast
from types import MappingProxyType
from bisect import insort
from struct import pack

from numpy import matrix, float64
from numpy.typing import NDArray

from .. import binary
from ._bmtr import BmtrFile, BmtrFrame
from ._common import (
    Bone,
    BoneStructure,
    BoneSequence,
    RtmProperty,
    RtmVector,
    RtmMatrix,
    _rot_loc_to_matrix
)


class RtmError(Exception):
    """Exception raised upon RTM reading and writing errors."""

    def __str__(self) -> str:
        return f"RTM - {super().__str__()}"


def _structure_to_bones_parents(
    skeleton: BoneStructure,
    parent: str = ""
) -> list[Bone]:
    """
    Converts a bone hierarchy structure to a flat sequence, like the
    bone list in a `model.cfg`.

    :param skeleton: Bone hierarchy
    :type skeleton: BoneStructure
    :param parent: Name of parent bone, defaults to ""
    :type parent: str, optional
    :return: Flattened bone-parent sequence
    :rtype: list[Bone]
    """
    result: list[Bone] = []
    if len(skeleton) == 0:
        return result

    for bone in skeleton:
        result.append(Bone(bone, parent))
        result.extend(_structure_to_bones_parents(skeleton[bone], bone))

    return result


def _multiply_matrices_np(m1: RtmMatrix, m2: RtmMatrix) -> RtmMatrix:
    """
    Multiplies two matrices with NumPy.

    :param m1: Left matrix
    :type m1: RtmMatrix
    :param m2: Right matrix
    :type m2: RtmMatrix
    :return: Multiplication result
    :rtype: RtmMatrix
    """
    result: NDArray[float64] = matrix(m1) @ matrix(m2)

    return cast(
        RtmMatrix,
        tuple(
            [tuple(row) for row in result.tolist()]
        )
    )


def _multiply_matrices(m1: RtmMatrix, m2: RtmMatrix) -> RtmMatrix:
    """
    Multiplies two 3x3 matrices with pure Python implementation.

    :param m1: Left matrix
    :type m1: RtmMatrix
    :param m2: Right matrix
    :type m2: RtmMatrix
    :return: Multiplication result
    :rtype: RtmMatrix
    """
    return (
        (
            m1[0][0]*m2[0][0] + m1[0][1]*m2[1][0]
            + m1[0][2]*m2[2][0] + m1[0][3]*m2[3][0],
            m1[0][0]*m2[0][1] + m1[0][1]*m2[1][1]
            + m1[0][2]*m2[2][1] + m1[0][3]*m2[3][1],
            m1[0][0]*m2[0][2] + m1[0][1]*m2[1][2]
            + m1[0][2]*m2[2][2] + m1[0][3]*m2[3][2],
            m1[0][0]*m2[0][3] + m1[0][1]*m2[1][3]
            + m1[0][2]*m2[2][3] + m1[0][3]*m2[3][3]
        ), (
            m1[1][0]*m2[0][0] + m1[1][1]*m2[1][0]
            + m1[1][2]*m2[2][0] + m1[1][3]*m2[3][0],
            m1[1][0]*m2[0][1] + m1[1][1]*m2[1][1]
            + m1[1][2]*m2[2][1] + m1[1][3]*m2[3][1],
            m1[1][0]*m2[0][2] + m1[1][1]*m2[1][2]
            + m1[1][2]*m2[2][2] + m1[1][3]*m2[3][2],
            m1[1][0]*m2[0][3] + m1[1][1]*m2[1][3]
            + m1[1][2]*m2[2][3] + m1[1][3]*m2[3][3]
        ), (
            m1[2][0]*m2[0][0] + m1[2][1]*m2[1][0]
            + m1[2][2]*m2[2][0] + m1[2][3]*m2[3][0],
            m1[2][0]*m2[0][1] + m1[2][1]*m2[1][1]
            + m1[2][2]*m2[2][1] + m1[2][3]*m2[3][1],
            m1[2][0]*m2[0][2] + m1[2][1]*m2[1][2]
            + m1[2][2]*m2[2][2] + m1[2][3]*m2[3][2],
            m1[2][0]*m2[0][3] + m1[2][1]*m2[1][3]
            + m1[2][2]*m2[2][3] + m1[2][3]*m2[3][3]
        ), (
            m1[3][0]*m2[0][0] + m1[3][1]*m2[1][0]
            + m1[3][2]*m2[2][0] + m1[3][3]*m2[3][0],
            m1[3][0]*m2[0][1] + m1[3][1]*m2[1][1]
            + m1[3][2]*m2[2][1] + m1[3][3]*m2[3][1],
            m1[3][0]*m2[0][2] + m1[3][1]*m2[1][2]
            + m1[3][2]*m2[2][2] + m1[3][3]*m2[3][2],
            m1[3][0]*m2[0][3] + m1[3][1]*m2[1][3]
            + m1[3][2]*m2[2][3] + m1[3][3]*m2[3][3]
        )
    )


_identity_bytes: bytes = pack(
    "<12f",
    1.0, 0.0, 0.0,
    0.0, 1.0, 0.0,
    0.0, 0.0, 1.0,
    0.0, 0.0, 0.0
)
"""Serialized 4x3 identity matrix."""


class RtmFrame:
    """
    Animation frame at a given phase, containing the transformation data
    for all bones.
    """

    def __init__(
        self,
        phase: float,
        bones: tuple[str, ...]
    ) -> None:
        """
        :param phase: Animation phase
        :type phase: float
        :param bones: Bones animated in the frame
        :type bones: tuple[str, ...]
        :raises RtmError: Duplicate bones
        """
        if len(set(bones)) != len(bones):
            raise RtmError(
                f"Cannot create frame with duplicate bones: {bones}"
            )

        self._phase = phase
        self._transforms: dict[str, RtmMatrix | None] = {
            name: None
            for name in bones
        }

    @property
    def phase(self) -> float:
        """
        :return: Animation phase
        :rtype: float
        """
        return self._phase

    @property
    def transforms(self) -> MappingProxyType[str, RtmMatrix | None]:
        """
        :return: Bone transformations
        :rtype: MappingProxyType[str, RtmMatrix | None]
        """
        return MappingProxyType(self._transforms)

    def set_transform(
        self,
        bone: str,
        matrix: RtmMatrix | None
    ) -> None:
        """
        Sets the transformation matrix of a bone.

        :param bone: Name of bone
        :type bone: str
        :param matrix: New transformation matrix
        :type matrix: RtmMatrix | None
        :raises ValueError: Bone not found in frame
        """
        if bone not in self._transforms:
            raise ValueError(
                f"'{bone}' is not an existing bone in the frame"
            )

        self._transforms[bone] = matrix

    @staticmethod
    def _read_matrix(stream: IO[bytes]) -> RtmMatrix:
        """
        Reads a transformation matrix from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :return: 4x4 transformation matrix
        :rtype: RtmMatrix
        """
        m = binary.read_floats(stream, 12)

        return (
            (m[0], m[1], m[2], 0.0),
            (m[3], m[4], m[5], 0.0),
            (m[6], m[7], m[8], 0.0),
            (m[9], m[10], m[11], 1.0)
        )

    @staticmethod
    def _write_matrix(stream: IO[bytes], m: RtmMatrix) -> None:
        """
        Writes a transformation matrix to a binary stream.

        :param stream: Target binary stream
        :type stream: IO[bytes]
        :param m: Transformation matrix
        :type m: RtmMatrix
        """
        binary.write_float(
            stream,
            m[0][0], m[0][1], m[0][2],
            m[1][0], m[1][1], m[1][2],
            m[2][0], m[2][1], m[2][2],
            m[3][0], m[3][1], m[3][2]
        )

    @classmethod
    def read(cls, stream: IO[bytes], bones: tuple[str, ...]) -> Self:
        """
        Reads an animation frame from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :param bones: List of expected bones
        :type bones: tuple[str, ...]
        :raises RtmError: The bones read did not match the bones provided
        :return: Animation frame
        :rtype: Self
        """
        phase = binary.read_float(stream)
        output = cls(phase, bones)

        output._transforms = {
            binary.read_asciiz_field(stream, 32): cls._read_matrix(stream)
            for _ in range(len(bones))
        }

        transform_bones = tuple(output._transforms.keys())
        if bones != transform_bones:
            raise RtmError(
                f"Mismatching bones or bone order between file {bones} "
                f"and frame {transform_bones}"
            )

        return output

    def write(self, stream: IO[bytes]) -> None:
        """
        Writes an animation frame to a binary stream.

        :param stream: Target binary stream
        :type stream: IO[bytes]
        """
        binary.write_float(stream, self._phase)
        for bone, mat in self._transforms.items():
            binary.write_asciiz_field(stream, bone, 32)
            if mat is None:
                stream.write(_identity_bytes)
            else:
                self._write_matrix(
                    stream,
                    mat
                )

    @classmethod
    def from_binarized(
        cls,
        frame_bmtr: BmtrFrame,
        bones: tuple[str, ...],
        skeleton: BoneStructure | BoneSequence
    ) -> Self:
        """
        Converts a frame from a binarized RTM to a plain frame.

        .. note::

            Plain animations store transformations are absolute 3D
            transformation matrices, while the binarized format stores them
            as relative quaternion-vector pairs. Therefore the perform the
            conversion, the skeleton bone hierarchy must be known.

        :param frame_bmtr: Binarized (BMTR) frame
        :type frame_bmtr: BmtrFrame
        :param bones: List of bones
        :type bones: tuple[str, ...]
        :param skeleton: Skeleton structure data
        :type skeleton: BoneStructure | BoneSequence
        :return: Converted frame
        :rtype: Self
        """
        frame_rtm = cls(frame_bmtr.phase, bones)
        for bone, transform in frame_bmtr.transforms.items():
            if transform is None:
                continue

            rot, loc = transform
            frame_rtm.set_transform(
                bone,
                _rot_loc_to_matrix(rot, loc)
            )

        if isinstance(skeleton, dict):
            skeleton = tuple(_structure_to_bones_parents(skeleton))

        for item in skeleton:
            mat = frame_rtm._transforms.get(item.name)
            if mat is None:
                continue

            mat_parent = frame_rtm._transforms.get(item.parent)
            if mat_parent is None:
                continue

            mat_final = _multiply_matrices(mat, mat_parent)
            frame_rtm.set_transform(item.name, mat_final)

        return frame_rtm


class RtmFile:
    """
    Animation data read from a plain RTM file.
    """

    def __init__(self) -> None:
        self._props: list[RtmProperty] = []
        self._source: str | None = None
        self._frames: list[RtmFrame] = []
        self._motion: RtmVector = RtmVector(0.0, 0.0, 0.0)
        self._bones: tuple[str, ...] | None = None

    @property
    def source(self) -> str | None:
        """
        :return: Path to source file (None if not read from file)
        :rtype: str | None
        """
        return self._source

    @property
    def bones(self) -> tuple[str, ...] | None:
        """
        :return: Bones in the animation (None if there are no frames)
        :rtype: tuple[str, ...] | None
        """
        return self._bones

    @property
    def properties(self) -> tuple[tuple[float, str, str], ...]:
        """
        :return: Phase-linked animation properties
        :rtype: tuple[tuple[float, str, str], ...]
        """
        return tuple(sorted(self._props, key=lambda x: x[0]))

    def add_property(self, phase: float, name: str, value: str) -> None:
        """
        Adds a new animation property.

        :param phase: Animation phase to link to
        :type phase: float
        :param name: Property name
        :type name: str
        :param value: Property value
        :type value: str
        """
        insort(
            self._props,
            RtmProperty(phase, name, value),
            key=lambda x: x.phase
        )

    def pop_property(self, idx: int) -> RtmProperty:
        """
        Removes and returns the property at the given index.

        :param idx: Index to remove
        :type idx: int
        :return: Removed property
        :rtype: RtmProperty
        """
        return self._props.pop(idx)

    @property
    def motion(self) -> RtmVector:
        """
        :return: Motion vector
        :rtype: RtmVector
        """
        return self._motion

    @motion.setter
    def motion(self, xyz: tuple[float, float, float] | RtmVector) -> None:
        if isinstance(xyz, RtmVector):
            self._motion = xyz
            return

        self._motion = RtmVector(xyz[0], xyz[1], xyz[2])

    @property
    def frames(self) -> tuple[RtmFrame, ...]:
        """
        :return: Animation frames
        :rtype: tuple[RtmFrame, ...]
        """
        return tuple(sorted(self._frames, key=lambda x: x.phase))

    def add_frame(self, frame: RtmFrame) -> None:
        """
        Adds a new frame to the animation.

        :param frame: Frame to add
        :type frame: RtmFrame
        :raises ValueError: Bones in frame did not match the expected bones
        """
        if len(self._frames) == 0:
            self._bones = tuple(frame.transforms.keys())
            self._frames.append(frame)
            return

        frame_bones = tuple(frame.transforms.keys())
        if frame_bones != self._bones:
            raise ValueError(
                "Cannot add frame with mismatching bones or bone order, "
                f"expected: {self._bones} got: {frame_bones}"
            )

        insort(self._frames, frame, key=lambda x: x.phase)

    def pop_frame(self, idx: int) -> RtmFrame:
        """
        Removes and returns the frame at the given index.

        :param idx: Index to remove.
        :type idx: int
        :return: Frame removed.
        :rtype: RtmFrame
        """
        frame = self._frames.pop(idx)
        if len(self._frames) == 0:
            self._bones = None

        return frame

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads animation data from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :raises RtmError: Stream is not valid RTM data
        :return: Animation data
        :rtype: Self
        """
        output = cls()
        signature = binary.read_char(stream, 8)
        if signature == "RTM_MDAT":
            stream.read(4)  # unknown padding
            count_props = binary.read_ulong(stream)
            props: list[RtmProperty] = []
            for _ in range(count_props):
                phase = binary.read_float(stream)
                name = binary.read_lascii(stream)
                value = binary.read_lascii(stream)
                props.append(RtmProperty(phase, name, value))

            output._props = sorted(props)
            signature = binary.read_char(stream, 8)

        if signature != "RTM_0101":
            raise RtmError(
                f"Unknown RTM block signature: {signature}"
            )

        x, y, z = binary.read_floats(stream, 3)
        output._motion = RtmVector(x, y, z)

        count_frames = binary.read_ulong(stream)
        count_bones = binary.read_ulong(stream)
        output._bones = tuple(
            [
                binary.read_asciiz_field(stream, 32)
                for _ in range(count_bones)
            ]
        )

        frames: list[RtmFrame] = [
            RtmFrame.read(stream, output._bones)
            for _ in range(count_frames)
        ]

        output._frames = sorted(frames, key=lambda x: x.phase)

        return output

    @classmethod
    def read_file(cls, filepath: str) -> Self:
        """
        Reads an RTM file at a given path.

        :param filepath: Path to RTM file
        :type filepath: str
        :return: Animation data
        :rtype: Self
        """
        with open(filepath, "rb") as file:
            output = cls.read(file)

        output._source = filepath

        return output

    @classmethod
    def from_binarized(
        cls,
        bmtr: BmtrFile,
        skeleton: BoneStructure | BoneSequence
    ) -> Self:
        """
        Converts data from a binarized RTM to plain data.

        .. note::

            Plain animations store transformations are absolute 3D
            transformation matrices, while the binarized format stores them
            as relative quaternion-vector pairs. Therefore the perform the
            conversion, the skeleton bone hierarchy must be known.

        :param bmtr: Binarized animation data
        :type bmtr: BmtrFile
        :param skeleton: Skeleton structure data
        :type skeleton: BoneStructure | BoneSequence
        :return: Animation data
        :rtype: Self
        """
        rtm = cls()

        for prop in bmtr.properties:
            rtm.add_property(
                prop.phase,
                prop.name,
                prop.value
            )

        rtm._source = bmtr.source
        rtm._motion = bmtr.motion
        rtm._bones = bmtr.bones

        if isinstance(skeleton, dict):
            skeleton = tuple(_structure_to_bones_parents(skeleton))

        for frame_bmtr in bmtr.frames:
            rtm.add_frame(
                RtmFrame.from_binarized(
                    frame_bmtr,
                    bmtr.bones,
                    skeleton
                )
            )

        return rtm

    def write(self, stream: IO[bytes]) -> None:
        """
        Writes animation data to a binary stream.

        :param stream: Target binary stream
        :type stream: IO[bytes]
        :raises RtmError: Data has no frames
        """
        if len(self._frames) == 0:
            raise RtmError("Cannot write RTM without frames")

        if len(self._props) > 0:
            binary.write_chars(stream, "RTM_MDAT")
            binary.write_ulong(stream, 0)
            binary.write_ulong(stream, len(self._props))
            for (phase, name, value) in self.properties:
                binary.write_float(stream, phase)
                binary.write_lascii(stream, name)
                binary.write_lascii(stream, value)

        binary.write_chars(stream, "RTM_0101")
        binary.write_float(stream, *self._motion)

        binary.write_ulong(stream, len(self._frames))
        bones: list[str] = list(self._frames[0].transforms.keys())
        binary.write_ulong(stream, len(bones))

        for name in bones:
            binary.write_asciiz_field(stream, name, 32)

        for frame in self._frames:
            frame.write(stream)

    def write_file(self, filepath: str) -> None:
        """
        Writes animation data to a specific file path.

        :param filepath: Path to RTM file
        :type filepath: str
        """
        with open(filepath, "wb") as file:
            self.write(file)
