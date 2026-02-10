from typing import Self, IO, NamedTuple, Any
from os import fspath
from struct import Struct
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..typing import StrOrBytesPath
from .. import binary


class P3dError(Exception):
    def __str__(self) -> str:
        return f"P3D - {super().__str__()}"


_VECTOR2D = Struct("<ff")
_VECTOR3D = Struct("<fff")
_VERTEX = Struct("<fffI")
_FACE = Struct("<IIff")


class P3dVector2d(NamedTuple):
    u: float
    v: float

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        u: float
        v: float
        u, v = _VECTOR2D.unpack(stream.read(8))
        return cls(u, v)

    def write(self, stream: IO[bytes]) -> None:
        stream.write(_VECTOR2D.pack(*self))


class P3dVector3d(NamedTuple):
    x: float
    y: float
    z: float

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        x: float
        y: float
        z: float
        x, y, z = _VECTOR3D.unpack(stream.read(12))
        return cls(x, y, z)

    def write(self, stream: IO[bytes]) -> None:
        stream.write(_VECTOR3D.pack(*self))


@dataclass(frozen=True)
class P3dVertex:
    point: P3dVector3d
    flags: int

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        x: float
        y: float
        z: float
        flags: int
        x, y, z, flags = _VERTEX.unpack(stream.read(16))
        return cls(P3dVector3d(x, y, z), flags)

    def write(self, stream: IO[bytes]) -> None:
        stream.write(_VERTEX.pack(*self.point, self.flags))


class P3dEdge(NamedTuple):
    v1: int
    v2: int


@dataclass(frozen=True)
class P3dFace:
    vertices: tuple[int, ...]
    normals: tuple[int, ...]
    uvs: tuple[P3dVector2d, ...]
    flags: int
    texture: str
    material: str

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        count_sides = binary.read_ulong(stream)
        assert 3 <= count_sides <= 4
        verts: list[int] = []
        normals: list[int] = []
        uvs: list[P3dVector2d] = []

        vert: int
        norm: int
        u: float
        v: float
        for _ in range(count_sides):
            vert, norm, u, v = _FACE.unpack(stream.read(16))
            verts.append(vert)
            normals.append(norm)
            uvs.append(P3dVector2d(u, v))

        stream.seek((4 - count_sides) * 16, 1)

        return cls(
            tuple(verts),
            tuple(normals),
            tuple(uvs),
            binary.read_ulong(stream),
            binary.read_asciiz(stream),
            binary.read_asciiz(stream)
        )

    def write(self, stream: IO[bytes]) -> None:
        count_sides = len(self.vertices)
        assert (
            3 <= count_sides <= 4
            and count_sides == len(self.normals) == len(self.uvs)
        )
        binary.write_ulong(stream, count_sides)
        for vert, norm, (u, v) in zip(
            self.vertices,
            self.normals,
            self.uvs
        ):
            stream.write(_FACE.pack(vert, norm, u, v))

        if count_sides == 4:
            stream.write(
                _FACE.pack(
                    self.vertices[-1],
                    self.normals[-1],
                    *self.uvs[-1]
                )
            )

        binary.write_ulong(stream, self.flags)
        binary.write_asciiz(stream, self.texture)
        binary.write_asciiz(stream, self.material)


class P3dTagg(ABC):
    @classmethod
    @abstractmethod
    def read(
        cls,
        stream: IO[bytes],
        *args: Any,
        **kwargs: Any
    ) -> Self: ...

    @abstractmethod
    def write(
        self,
        stream: IO[bytes]
    ) -> None: ...


class P3dUnknownTagg(P3dTagg):
    def __init__(self, name: str, raw: bytes) -> None:
        self._name = name
        self._raw = raw

    @property
    def name(self) -> str:
        return self._name

    @property
    def raw(self) -> bytes:
        return self._raw

    @classmethod
    def read(
        cls,
        stream: IO[bytes]
    ) -> Self:
        assert stream.read(1) == b"\x01"
        name = binary.read_asciiz(stream)
        length = binary.read_ulong(stream)
        return cls(
            name,
            stream.read(length)
        )

    def write(
        self,
        stream: IO[bytes]
    ) -> None:
        stream.write(b"\x01")
        binary.write_asciiz(stream, self._name)
        binary.write_ulong(stream, len(self._raw))
        stream.write(self._raw)


class P3dPropertyTagg(P3dTagg):
    def __init__(self, name: str, value: str) -> None:
        self._name = name
        self._value = value

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> str:
        return self._value

    @classmethod
    def read(
        cls,
        stream: IO[bytes]
    ) -> Self:
        assert stream.read(1) == b"\x01"
        assert binary.read_asciiz(stream) == "#Property#"
        assert binary.read_ulong(stream) == 128
        return cls(
            binary.read_asciiz_field(stream, 64),
            binary.read_asciiz_field(stream, 64)
        )

    def write(
        self,
        stream: IO[bytes]
    ) -> None:
        stream.write(b"\x01")
        binary.write_asciiz(stream, "#Property#")
        binary.write_ulong(stream, 128)
        binary.write_asciiz_field(stream, self._name, 64)
        binary.write_asciiz_field(stream, self._value, 64)


class P3dMassTagg(P3dTagg):
    def __init__(self, masses: tuple[float, ...]) -> None:
        self._masses = masses

    @property
    def masses(self) -> tuple[float, ...]:
        return self._masses

    @classmethod
    def read(
        cls,
        stream: IO[bytes],
        count_vertices: int
    ) -> Self:
        assert stream.read(1) == b"\x01"
        assert binary.read_asciiz(stream) == "#Mass#"
        assert binary.read_ulong(stream) == (count_vertices * 4)
        return cls(binary.read_floats(stream, count_vertices))

    def write(
        self,
        stream: IO[bytes]
    ) -> None:
        stream.write(b"\x01")
        binary.write_asciiz(stream, "#Mass#")
        binary.write_ulong(stream, len(self._masses) * 4)
        binary.write_float(stream, *self._masses)


class P3dEofTagg(P3dTagg):
    @classmethod
    def read(
        cls,
        stream: IO[bytes]
    ) -> Self:
        assert stream.read(1) == b"\x01"
        assert binary.read_asciiz(stream) == "#EndOfFile#"

        length = binary.read_ulong(stream)
        assert length == 0

        return cls()

    def write(
        self,
        stream: IO[bytes]
    ) -> None:
        stream.write(b"\x01")
        binary.write_asciiz(stream, "#EndOfFile#")
        binary.write_ulong(stream, 0)


def _read_tagg(
    stream: IO[bytes],
    count_vertices: int,
    count_faces: int,
    *,
    keep_unknown: bool = False
) -> P3dTagg | None:
    start = stream.tell()
    assert stream.read(1) == b"\x01"
    name = binary.read_asciiz(stream)
    stream.seek(start)

    match name:
        case "#EndOfFile#":
            return P3dEofTagg.read(stream)
        case "#Property#":
            return P3dPropertyTagg.read(stream)
        case "#Mass#":
            return P3dMassTagg.read(stream, count_vertices)
        case _ if keep_unknown:
            return P3dUnknownTagg.read(stream)
        case _:
            return None


class P3dLod:
    def __init__(self) -> None:
        self._verts: tuple[P3dVertex, ...] = ()
        self._normals: tuple[P3dVector3d, ...] = ()
        self._faces: tuple[P3dFace, ...] = ()
        self._flags: int = 0
        self._taggs: list[P3dTagg] = []
        self._resolution: float = 0.0

    @classmethod
    def read(
        cls,
        stream: IO[bytes],
        *,
        keep_unknown_taggs: bool = False
    ) -> Self:
        if (signature := stream.read(4)) != b"P3DM":
            raise P3dError(
                f"Unsupported LOD type: {signature!r}"
            )

        if (version := binary.read_ulongs(stream, 2)) != (0x1c, 0x100):
            raise P3dError(
                f"Unsupported LOD version: {version[0]}.{version[1]}"
            )

        (
            count_verts,
            count_normals,
            count_faces,
            flags
        ) = binary.read_ulongs(stream, 4)
        output = cls()
        output._flags = flags
        output._verts = tuple(
            [
                P3dVertex.read(stream)
                for _ in range(count_verts)
            ]
        )
        output._normals = tuple(
            [
                P3dVector3d.read(stream)
                for _ in range(count_normals)
            ]
        )
        output._faces = tuple(
            [
                P3dFace.read(stream)
                for _ in range(count_faces)
            ]
        )
        if (tagg_signature := stream.read(4)) != b"TAGG":
            raise P3dError(
                f"Invalid TAGG signature: {tagg_signature!r}"
            )

        while True:
            tagg = _read_tagg(
                stream,
                count_verts,
                count_faces,
                keep_unknown=keep_unknown_taggs
            )
            if tagg is None:
                continue

            output._taggs.append(tagg)
            if isinstance(tagg, P3dEofTagg):
                break

        output._resolution = binary.read_float(stream)

        return output


class P3dFile:
    def __init__(self) -> None:
        self._source: str | bytes | None
        self._lods: list[P3dLod] = []

    @property
    def source(self) -> str | bytes | None:
        return self._source

    @classmethod
    def read(
        cls,
        stream: IO[bytes],
        *,
        first_lod_only: bool = False,
        keep_unknown_taggs: bool = False
    ) -> Self:
        if (signature := stream.read(4)) != b"MLOD":
            raise P3dError(
                f"Invalid signature: {signature!r}"
            )

        if (version := binary.read_ulong(stream)) != 257:
            raise P3dError(
                f"Unsupported P3D version: {version:d}"
            )

        output = cls()
        count_lods = binary.read_ulong(stream)
        if first_lod_only:
            count_lods = 1

        output._lods = [
            P3dLod.read(
                stream,
                keep_unknown_taggs=keep_unknown_taggs
            )
            for _ in range(count_lods)
        ]

        return output

    @classmethod
    def read_file(
        cls,
        filepath: StrOrBytesPath,
        *,
        first_lod_only: bool = False,
        keep_unknown_taggs: bool = False
    ) -> Self:
        with open(filepath, "rb") as file:
            output = cls.read(
                file,
                first_lod_only=first_lod_only,
                keep_unknown_taggs=keep_unknown_taggs
            )

        output._source = fspath(filepath)
        return output
