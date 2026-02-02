from typing import Self, IO
from types import MappingProxyType
from io import BytesIO

from .. import binary
from ..compression import lzo1x_decompress
from ._common import RtmQuaternion, RtmVector, RtmProperty


class BmtrError(Exception):
    """Exception raised upon BMTR reading errors."""

    def __str__(self) -> str:
        return f"BMTR - {super().__str__()}"


class BmtrFrame:
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
        :raises BmtrError: Duplicate bones
        """
        if len(set(bones)) != len(bones):
            raise BmtrError(
                f"Cannot create frame with duplicate bones: {bones}"
            )

        self._phase = phase
        self._transforms: dict[str, tuple[RtmQuaternion, RtmVector] | None] = {
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
    def transforms(self) -> MappingProxyType[
        str,
        tuple[RtmQuaternion, RtmVector] | None
    ]:
        """
        :return: Bone transformations
        :rtype: ~types.MappingProxyType[str,
            tuple[RtmQuaternion, RtmVector] | None]
        """
        return MappingProxyType(self._transforms)

    @staticmethod
    def _read_transform(
        stream: IO[bytes]
    ) -> tuple[RtmQuaternion, RtmVector]:
        """
        Reads a quaternion-vector pair from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :return: Transformation data
        :rtype: tuple[RtmQuaternion, RtmVector]
        """
        q1, q2, q3, q4 = binary.read_shorts(stream, 4)
        quaternion = RtmQuaternion(
            q1 / 16384,
            q2 / 16384,
            q3 / 16384,
            q4 / 16384
        )
        x, y, z = binary.read_halfs(stream, 3)
        vec = RtmVector(x, y, z)
        return (
            quaternion,
            vec
        )

    @classmethod
    def read(
        cls,
        stream: IO[bytes],
        phase: float,
        bones: tuple[str, ...]
    ) -> Self:
        """
        Reads an animation frame from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :param phase: Animation phase
        :type phase: float
        :param bones: List of expected bones
        :type bones: tuple[str, ...]
        :return: Animation frame
        :rtype: Self
        """
        output = cls(phase, bones)
        output._transforms = {
            name: cls._read_transform(stream)
            for name in bones
        }

        return output


class BmtrFile:
    """
    Animation data read from a binarized RTM file.
    """

    def __init__(self) -> None:
        self._source: str | None = None
        self._version: int = 5
        self._motion: RtmVector = RtmVector(0.0, 0.0, 0.0)
        self._bones: tuple[str, ...] = ()
        self._frames: tuple[BmtrFrame, ...] = ()
        self._props: tuple[RtmProperty, ...] = ()

    @property
    def source(self) -> str | None:
        """
        :return: Path to source file (None if not read from file)
        :rtype: str | None
        """
        return self._source

    @property
    def version(self) -> int:
        """
        :return: Format version
        :rtype: int
        """
        return self._version

    @property
    def motion(self) -> RtmVector:
        """
        :return: Motion vector
        :rtype: RtmVector
        """
        return self._motion

    @property
    def bones(self) -> tuple[str, ...]:
        """
        :return: Bones in the animation
        :rtype: tuple[str, ...]
        """
        return self._bones

    @property
    def frames(self) -> tuple[BmtrFrame, ...]:
        """
        :return: Animation frames
        :rtype: tuple[RtmFrame, ...]
        """
        return self._frames

    @property
    def properties(self) -> tuple[RtmProperty, ...]:
        """
        :return: Phase-linked animation properties
        :rtype: tuple[tuple[float, str, str], ...]
        """
        return self._props

    def _read_phases(
        self,
        stream: IO[bytes],
        count: int
    ) -> tuple[float, ...]:
        """
        Reads frame phase list from a binary stream.

        :param stream: Source binary stream.
        :type stream: IO[bytes]
        :param count: Number of phases to read
        :type count: int
        :raises BmtrError: Error occured during decompression
        :return: Animation frame phases
        :rtype: tuple[float, ...]
        """
        expected_data = count * 4
        compressed = expected_data >= 1024
        if self.version >= 4:
            compressed = binary.read_bool(stream)

        phases: list[float] = []
        if compressed:
            try:
                _, decompressed = lzo1x_decompress(stream, expected_data)
            except Exception as e:
                raise BmtrError("Could not decompress phase list") from e

            buffer = BytesIO(decompressed)
            phases = [binary.read_float(buffer) for _ in range(count)]
            if buffer.read() != b"":
                raise BmtrError(
                    "Decompressed phase list data was longer than expected"
                )
        else:
            phases = [binary.read_float(stream) for _ in range(count)]

        return tuple(phases)

    def _read_frames(
        self,
        stream: IO[bytes],
        phases: tuple[float, ...],
        bones: tuple[str, ...]
    ) -> None:
        """
        Reads animation frames from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :param phases: Animation frame phases
        :type phases: tuple[float, ...]
        :param bones: List of expected bones
        :type bones: tuple[str, ...]
        :raises BmtrError: Error occured during decompression
        """
        frames: list[BmtrFrame] = []
        for phase in phases:
            count_bones = binary.read_ulong(stream)
            expected_data = count_bones * 14
            compressed = expected_data >= 1024
            if self.version >= 4:
                compressed = binary.read_bool(stream)

            if compressed:
                try:
                    _, decompressed = lzo1x_decompress(stream, expected_data)
                except Exception as e:
                    raise BmtrError("Could not decompress frame data") from e

                buffer = BytesIO(decompressed)
                frames.append(BmtrFrame.read(buffer, phase, bones))
                if buffer.read() != b"":
                    raise BmtrError(
                        "Decompressed frame data was longer than expected"
                    )
            else:
                frames.append(BmtrFrame.read(stream, phase, bones))

        self._frames = tuple(frames)

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        """
        Reads binarized animation data from a binary stream.

        :param stream: Source binary stream
        :type stream: IO[bytes]
        :raises BmtrError: Stream is not valid animation data
        :return: Animation data
        :rtype: Self
        """
        signature = binary.read_char(stream, 4)
        if signature != "BMTR":
            raise BmtrError(
                f"Not a valid BMTR file, invalid signature: {signature}"
            )

        output = cls()
        version = binary.read_ulong(stream)
        if version not in (3, 4, 5):
            raise BmtrError(
                f"Unsupported BMTR version: {version}"
            )

        stream.read(1)
        x, y, z = binary.read_floats(stream, 3)
        output._motion = RtmVector(x, y, z)

        count_frames = binary.read_ulong(stream)
        stream.read(4)
        count_bones = binary.read_ulong(stream)
        stream.read(4)  # bone count again?
        bones = [
            binary.read_asciiz(stream)
            for _ in range(count_bones)
        ]
        output._bones = tuple(bones)

        if version >= 4:
            stream.read(4)  # always 0
            count_props = binary.read_ulong(stream)
            props: list[RtmProperty] = []
            for _ in range(count_props):
                stream.read(4)  # always 0xffffffff
                name = binary.read_asciiz(stream)
                phase = binary.read_float(stream)
                value = binary.read_asciiz(stream)
                props.append(RtmProperty(phase, name, value))

            output._props = tuple(props)

        stream.read(4)  # phase count?

        phases = output._read_phases(stream, count_frames)
        output._read_frames(stream, phases, output._bones)

        if stream.read() != b"":
            raise BmtrError(
                "EOF not found"
            )

        return output

    @classmethod
    def read_file(cls, filepath: str) -> Self:
        """
        Reads animation data from a binarized RTM file at a given path.

        :param filepath: Path to RTM file
        :type filepath: str
        :return: Animation data
        :rtype: Self
        """
        with open(filepath, "rb") as file:
            output = cls.read(file)

        output._source = filepath

        return output
