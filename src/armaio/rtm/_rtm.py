from typing import Self, IO, TypeAlias, NamedTuple
from types import MappingProxyType
from bisect import insort
from struct import pack

from .. import binary


class RtmError(Exception):
    def __str__(self) -> str:
        return f"RTM - {super().__str__()}"


RtmMatrix: TypeAlias = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float]
]


_identity: bytes = pack(
    "<12f",
    1.0, 0.0, 0.0,
    0.0, 1.0, 0.0,
    0.0, 0.0, 1.0,
    0.0, 0.0, 0.0
)


class RtmProperty(NamedTuple):
    phase: float
    name: str
    value: str


class RtmVector(NamedTuple):
    x: float
    y: float
    z: float


class RtmFrame:
    def __init__(
        self,
        phase: float,
        bones: tuple[str, ...]
    ) -> None:
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
        return self._phase

    @property
    def transforms(self) -> MappingProxyType[str, RtmMatrix | None]:
        return MappingProxyType(self._transforms)

    def set_transform(
        self,
        bone: str,
        matrix: RtmMatrix | None
    ) -> None:
        if bone not in self._transforms:
            raise ValueError(
                f"'{bone}' is not an existing bone in the frame"
            )

        self._transforms[bone] = matrix

    @staticmethod
    def _read_matrix(stream: IO[bytes]) -> RtmMatrix:
        m = binary.read_floats(stream, 12)

        return (
            (m[0], m[1], m[2], 0.0),
            (m[3], m[4], m[5], 0.0),
            (m[6], m[7], m[8], 0.0),
            (m[9], m[10], m[11], 1.0)
        )

    @staticmethod
    def _write_matrix(stream: IO[bytes], m: RtmMatrix) -> None:
        binary.write_float(
            stream,
            m[0][0], m[0][1], m[0][2],
            m[1][0], m[1][1], m[1][2],
            m[2][0], m[2][1], m[2][2],
            m[3][0], m[3][1], m[3][2]
        )

    @classmethod
    def read(cls, stream: IO[bytes], bones: tuple[str, ...]) -> Self:
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
        binary.write_float(stream, self._phase)
        for bone, matrix in self._transforms.items():
            binary.write_asciiz_field(stream, bone, 32)
            if matrix is None:
                stream.write(_identity)
            else:
                self._write_matrix(
                    stream,
                    matrix
                )


class RtmFile:
    def __init__(self) -> None:
        self._props: list[RtmProperty] = []
        self._source: str | None = None
        self._frames: list[RtmFrame] = []
        self._motion: RtmVector = RtmVector(0.0, 0.0, 0.0)
        self._bones: tuple[str, ...] | None = None

    @property
    def source(self) -> str | None:
        return self._source

    @property
    def bones(self) -> tuple[str, ...] | None:
        return self._bones

    @property
    def properties(self) -> tuple[tuple[float, str, str], ...]:
        return tuple(sorted(self._props, key=lambda x: x[0]))

    def add_property(self, phase: float, name: str, value: str) -> None:
        insort(
            self._props,
            RtmProperty(phase, name, value),
            key=lambda x: x.phase
        )

    def pop_property(self, idx: int) -> RtmProperty:
        return self._props.pop(idx)

    @property
    def motion(self) -> RtmVector:
        return self._motion

    @motion.setter
    def motion(self, xyz: tuple[float, float, float] | RtmVector) -> None:
        if isinstance(xyz, RtmVector):
            self._motion = xyz
            return

        self._motion = RtmVector(xyz[0], xyz[1], xyz[2])

    @property
    def frames(self) -> tuple[RtmFrame, ...]:
        return tuple(sorted(self._frames, key=lambda x: x.phase))

    def add_frame(self, frame: RtmFrame) -> None:
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
        frame = self._frames.pop(idx)
        if len(self._frames) == 0:
            self._bones = None

        return frame

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
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
        with open(filepath, "rb") as file:
            output = cls.read(file)

        output._source = filepath

        return output

    def write(self, stream: IO[bytes]) -> None:
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
        with open(filepath, "wb") as file:
            self.write(file)
