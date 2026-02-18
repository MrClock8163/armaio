from typing import Self, IO, NamedTuple, Any, TypeAlias
from os import fspath
from struct import Struct
from dataclasses import dataclass
from abc import ABC, abstractmethod
from math import sqrt

from ..typing import StrOrBytesPath
from .. import binary


class P3dError(Exception):
    def __str__(self) -> str:
        return f"P3D - {super().__str__()}"


_STRUCT_VECTOR2D = Struct("<ff")
_STRUCT_VECTOR3D = Struct("<fff")
_STRUCT_VERTEX = Struct("<fffI")
_STRUCT_FACE = Struct("<IIffIIffIIffIIff")

_FACEVERTS: TypeAlias = tuple[
    int, int, float, float,
    int, int, float, float,
    int, int, float, float,
    int, int, float, float
]


class P3dVector2d(NamedTuple):
    u: float
    v: float

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        u: float
        v: float
        u, v = _STRUCT_VECTOR2D.unpack(stream.read(8))
        return cls(u, v)

    def write(self, stream: IO[bytes]) -> None:
        stream.write(_STRUCT_VECTOR2D.pack(*self))

    def normalized(self) -> Self:
        length = sqrt(self.u**2 + self.v ** 2)
        if length == 0.0:
            return type(self)(self.u, self.v)

        return type(self)(self.u / length, self.v / length)


class P3dVector3d(NamedTuple):
    x: float
    y: float
    z: float

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        x: float
        y: float
        z: float
        x, y, z = _STRUCT_VECTOR3D.unpack(stream.read(12))
        return cls(x, y, z)

    def write(self, stream: IO[bytes]) -> None:
        stream.write(_STRUCT_VECTOR3D.pack(*self))

    def normalized(self) -> Self:
        length = sqrt(self.x**2 + self.y ** 2 + self.z**2)
        if length == 0.0:
            return type(self)(self.x, self.y, self.z)

        return type(self)(self.x / length, self.y / length, self.x / length)


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
        x, y, z, flags = _STRUCT_VERTEX.unpack(stream.read(16))
        return cls(P3dVector3d(x, y, z), flags)

    def write(self, stream: IO[bytes]) -> None:
        stream.write(_STRUCT_VERTEX.pack(*self.point, self.flags))


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

        verts_table: _FACEVERTS = _STRUCT_FACE.unpack(stream.read(16 * 4))
        verts: list[int] = [
            verts_table[0],
            verts_table[4],
            verts_table[8]
        ]
        normals: list[int] = [
            verts_table[1],
            verts_table[5],
            verts_table[9]
        ]
        uvs: list[P3dVector2d] = [
            P3dVector2d(verts_table[2], verts_table[3]),
            P3dVector2d(verts_table[6], verts_table[7]),
            P3dVector2d(verts_table[10], verts_table[11])
        ]
        if count_sides > 3:
            verts.append(verts_table[12])
            normals.append(verts_table[13])
            uvs.append(
                P3dVector2d(verts_table[14], verts_table[15])
            )

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
        stream.write(
            _STRUCT_FACE.pack(
                self.vertices[0],
                self.normals[0],
                self.uvs[0].u,
                self.uvs[0].v,
                self.vertices[1],
                self.normals[1],
                self.uvs[1].u,
                self.uvs[1].v,
                self.vertices[2],
                self.normals[2],
                self.uvs[2].u,
                self.uvs[2].v,
                self.vertices[2] if count_sides == 3 else self.vertices[3],
                self.normals[2] if count_sides == 3 else self.normals[3],
                self.uvs[2].u if count_sides == 3 else self.uvs[3].u,
                self.uvs[2].v if count_sides == 3 else self.uvs[3].v
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

    @abstractmethod
    def validate(
        self,
        count_verts: int,
        count_tris: int,
        count_quads: int,
        *,
        strict: bool
    ) -> bool: ...


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

    def validate(
        self,
        count_verts: int,
        count_tris: int,
        count_quads: int,
        *,
        strict: bool
    ) -> bool:
        return True

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

    def validate(
        self,
        count_verts: int,
        count_tris: int,
        count_quads: int,
        *,
        strict: bool
    ) -> bool:
        return len(self._name) < 64 and len(self._value) < 64

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

    def validate(
        self,
        count_verts: int,
        count_tris: int,
        count_quads: int,
        *,
        strict: bool
    ) -> bool:
        return len(self._masses) == count_verts

    def write(
        self,
        stream: IO[bytes]
    ) -> None:
        stream.write(b"\x01")
        binary.write_asciiz(stream, "#Mass#")
        binary.write_ulong(stream, len(self._masses) * 4)
        binary.write_float(stream, *self._masses)


class P3dSharpEdgesTagg(P3dTagg):
    def __init__(self, edges: tuple[P3dEdge, ...]) -> None:
        self._edges = edges

    @property
    def edges(self) -> tuple[P3dEdge, ...]:
        return self._edges

    @classmethod
    def read(
        cls,
        stream: IO[bytes]
    ) -> Self:
        assert stream.read(1) == b"\x01"
        assert binary.read_asciiz(stream) == "#SharpEdges#"

        length = binary.read_ulong(stream)
        count_values = length // 4
        data = binary.read_ulongs(stream, count_values)
        edges = [
            P3dEdge(data[i], data[i+1])
            for i in range(0, count_values, 2)
        ]

        return cls(tuple(edges))

    def validate(
        self,
        count_verts: int,
        count_tris: int,
        count_quads: int,
        *,
        strict: bool
    ) -> bool:
        if not strict:
            return True

        def valid_idx(idx: int) -> bool:
            return 0 <= idx < count_verts

        for v1, v2 in self._edges:
            if not (valid_idx(v1) and valid_idx(v2)):
                return False

        return True

    def write(
        self,
        stream: IO[bytes]
    ) -> None:
        stream.write(b"\x01")
        binary.write_asciiz(stream, "#SharpEdges#")
        binary.write_ulong(stream, len(self._edges) * 2 * 4)
        values = [
            x
            for edge in self._edges
            for x in edge
        ]
        binary.write_ulong(stream, *values)


class P3dUvSetTagg(P3dTagg):
    def __init__(
        self,
        index: int,
        coordinates: tuple[P3dVector2d, ...]
    ) -> None:
        self._index = index
        self._uvs = coordinates

    @property
    def index(self) -> int:
        return self._index

    @property
    def coordinates(self) -> tuple[P3dVector2d, ...]:
        return self._uvs

    @classmethod
    def read(cls, stream: IO[bytes]) -> Self:
        assert stream.read(1) == b"\x01"
        assert binary.read_asciiz(stream) == "#UVSet#"

        length, index = binary.read_ulongs(stream, 2)
        count_values = (length - 4) // 4
        data = binary.read_floats(stream, count_values)

        uvs = [
            P3dVector2d(data[i], data[i+1])
            for i in range(0, count_values, 2)
        ]

        return cls(index, tuple(uvs))

    def validate(
        self,
        count_verts: int,
        count_tris: int,
        count_quads: int,
        *,
        strict: bool
    ) -> bool:
        if self._index < 0:
            return False

        if len(self._uvs) != (count_tris * 3 + count_quads * 4):
            return False

        return True

    def write(
        self,
        stream: IO[bytes]
    ) -> None:
        stream.write(b"\x01")
        binary.write_asciiz(stream, "#UVSet#")
        binary.write_ulong(
            stream,
            len(self._uvs) * 2 * 4,
            self._index
        )
        values = [
            x
            for uv in self._uvs
            for x in uv
        ]
        binary.write_float(stream, *values)


class P3dSelectionTagg(P3dTagg):
    def __init__(self, name: str, count_verts: int, count_faces: int) -> None:
        self._name = name
        self._weights_verts: dict[int, float] = {}
        self._weights_faces: dict[int, float] = {}
        self._count_verts = count_verts
        self._count_faces = count_faces

    @property
    def name(self) -> str:
        return self._name

    @staticmethod
    def decode_weight(weight: int) -> float:
        if weight in (0, 1):
            return weight

        return (255 - weight) / 254

    @staticmethod
    def encode_weight(weight: float) -> int:
        if weight in (0, 1):
            return int(weight)

        value = round(255 - 254 * weight)

        return value

    @classmethod
    def read(
        cls,
        stream: IO[bytes],
        count_verts: int,
        count_faces: int,
        *,
        ignore_faces: bool = False
    ) -> Self:
        assert stream.read(1) == b"\x01"
        name = binary.read_asciiz(stream)
        assert not name.startswith("#") and not name.endswith("#")
        assert binary.read_ulong(stream) == count_verts + count_faces

        output = cls(name, count_verts, count_faces)

        for i, encoded in enumerate(stream.read(count_verts)):
            if (w := cls.decode_weight(encoded)) > 0:
                output._weights_verts[i] = w

        if ignore_faces:
            stream.seek(count_faces, 1)
        else:
            for i, encoded in enumerate(stream.read(count_faces)):
                if (w := cls.decode_weight(encoded)) > 0:
                    output._weights_faces[i] = w

        return output

    def validate(
        self,
        count_verts: int,
        count_tris: int,
        count_quads: int,
        *,
        strict: bool
    ) -> bool:
        idx_verts = list(self._weights_verts.keys())
        idx_faces = list(self._weights_faces.keys())

        if idx_verts:
            min_vert = min(idx_verts)
            max_vert = max(idx_verts)

            if not (
                0 <= min_vert < count_verts
                and 0 <= max_vert < count_verts
            ):
                return False

        if idx_faces:
            min_face = min(idx_faces)
            max_face = max(idx_faces)

            if not (
                0 <= min_face < (count_tris + count_quads)
                and 0 <= max_face < (count_tris + count_quads)
            ):
                return False

        return True

    def write(
        self,
        stream: IO[bytes]
    ) -> None:
        stream.write(b"\x01")
        binary.write_asciiz(stream, self._name)
        binary.write_ulong(stream, self._count_verts + self._count_faces)

        weights_verts = bytearray(self._count_verts)
        for i, w in self._weights_verts.items():
            weights_verts[i] = self.encode_weight(w)

        weights_faces = bytearray(self._count_faces)
        for i, w in self._weights_faces.items():
            weights_faces[i] = self.encode_weight(w)

        stream.write(weights_verts)
        stream.write(weights_faces)


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

    def validate(
        self,
        count_verts: int,
        count_tris: int,
        count_quads: int,
        *,
        strict: bool
    ) -> bool:
        return True

    def write(
        self,
        stream: IO[bytes]
    ) -> None:
        stream.write(b"\x01")
        binary.write_asciiz(stream, "#EndOfFile#")
        binary.write_ulong(stream, 0)


def _is_special_tagg(name: str) -> bool:
    return name.startswith("#") and name.endswith("#")


def _read_tagg(
    stream: IO[bytes],
    count_vertices: int,
    count_faces: int,
    *,
    keep_unknown: bool = False,
    ignore_face_weights: bool = False
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
        case "#SharpEdges#":
            return P3dSharpEdgesTagg.read(stream)
        case "#UVSet#":
            return P3dUvSetTagg.read(stream)
        case _ if _is_special_tagg(name) and keep_unknown:
            return P3dUnknownTagg.read(stream)
        case _ if _is_special_tagg(name):
            return None
        case _:
            return P3dSelectionTagg.read(
                stream,
                count_vertices,
                count_faces,
                ignore_faces=ignore_face_weights
            )


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
        keep_unknown_taggs: bool = False,
        ignore_face_weights: bool = False
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
                keep_unknown=keep_unknown_taggs,
                ignore_face_weights=ignore_face_weights
            )
            if tagg is None:
                continue

            output._taggs.append(tagg)
            if isinstance(tagg, P3dEofTagg):
                break

        output._resolution = binary.read_float(stream)

        return output

    def validate(
        self,
        *,
        strict: bool = False
    ) -> bool:
        count_verts = len(self._verts)
        count_normals = len(self._normals)

        def valid_vidx(idx: int) -> bool:
            return 0 <= idx < count_verts

        def valid_nidx(idx: int) -> bool:
            return 0 <= idx < count_normals

        count_tris = count_quads = 0
        for face in self._faces:
            sides = len(face.vertices)
            if sides == 3:
                count_tris += 1
            elif sides == 4:
                count_quads += 1
            else:
                return False

            for vidx, nidx in zip(face.vertices, face.vertices):
                if not (valid_vidx(vidx) and valid_nidx(nidx)):
                    return False

        for tagg in self._taggs:
            tagg.validate(
                count_verts,
                count_tris,
                count_quads,
                strict=strict
            )

        return True


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
        keep_unknown_taggs: bool = False,
        ignore_face_weights: bool = False
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
                keep_unknown_taggs=keep_unknown_taggs,
                ignore_face_weights=ignore_face_weights
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
        keep_unknown_taggs: bool = False,
        ignore_face_weights: bool = False
    ) -> Self:
        with open(filepath, "rb") as file:
            output = cls.read(
                file,
                first_lod_only=first_lod_only,
                keep_unknown_taggs=keep_unknown_taggs,
                ignore_face_weights=ignore_face_weights
            )

        output._source = fspath(filepath)
        return output

    def validate(
        self,
        *,
        strict: bool = False
    ) -> bool:
        for lod in self._lods:
            if not lod.validate(strict=strict):
                return False

        return True
