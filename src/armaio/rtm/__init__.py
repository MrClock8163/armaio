from typing import IO

from ._rtm import (  # noqa: F401
    RtmError as RtmError,
    RtmFrame as RtmFrame,
    RtmFile as RtmFile
)
from ._bmtr import (  # noqa: F401
    BmtrError as BmtrError,
    BmtrFrame as BmtrFrame,
    BmtrFile as BmtrFile
)
from ._common import (  # noqa: F401
    RtmProperty as RtmProperty,
    RtmMatrix as RtmMatrix,
    RtmVector as RtmVector,
    RtmQuaternion as RtmQuaternion,
    Bone as Bone,
    BoneStructure as BoneStructure,
    BoneSequence as BoneSequence,
    rot_loc_to_matrix as rot_loc_to_matrix
)


def read_rtm(
    stream: IO[bytes],
    skeleton: BoneStructure | BoneSequence
) -> RtmFile:
    """
    Reads RTM animation data from a binary stream.

    If the data is in binarized format, the conversion is done automatically.

    :param stream: Source binary stream
    :type stream: IO[bytes]
    :param skeleton: Skeleton structure data
    :type skeleton: BoneStructure | BoneSequence
    :return: Animation data
    :rtype: RtmFile
    """
    signature = stream.read(4)
    stream.seek(0)
    if signature != b"BMTR":
        stream.seek(0)
        return RtmFile.read(stream)

    bmtr = BmtrFile.read(stream)
    return RtmFile.from_binarized(
        bmtr,
        skeleton
    )


def read_rtm_file(
    filepath: str,
    skeleton: BoneStructure | BoneSequence
) -> RtmFile:
    """
    Reads RTM animation data from a file at a given path.

    If the data is in binarized format, the conversion is done automatically.

    :param filepath: Path to RTM file
    :type filepath: str
    :param skeleton: Skeleton structure data
    :type skeleton: BoneStructure | BoneSequence
    :return: Animation data
    :rtype: RtmFile
    """
    with open(filepath, "rb") as file:
        rtm = read_rtm(file, skeleton)
        rtm._source = filepath
        return rtm
