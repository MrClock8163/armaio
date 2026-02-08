from typing import IO
from os import fspath

from ..typing import StrOrBytesPath
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
    filepath: StrOrBytesPath,
    skeleton: BoneStructure | BoneSequence
) -> RtmFile:
    """
    Reads RTM animation data from a file at a given path.

    If the data is in binarized format, the conversion is done automatically.

    :param filepath: Path to RTM file
    :type filepath: StrOrBytesPath
    :param skeleton: Skeleton structure data
    :type skeleton: BoneStructure | BoneSequence
    :return: Animation data
    :rtype: RtmFile
    """
    with open(filepath, "rb") as file:
        rtm = read_rtm(file, skeleton)
        rtm._source = fspath(filepath)
        return rtm


OFP2_MANSKELETON: BoneSequence = (
    Bone("Pelvis", ""),
    Bone("Spine", "Pelvis"),
    Bone("Spine1", "Spine"),
    Bone("Spine2", "Spine1"),
    Bone("Spine3", "Spine2"),
    Bone("Camera", "Pelvis"),
    Bone("weapon", "Spine1"),
    Bone("launcher", "Spine1"),
    Bone("neck", "Spine3"),
    Bone("neck1", "neck"),
    Bone("head", "neck1"),
    Bone("Face_Hub", "head"),
    Bone("Face_Jawbone", "Face_Hub"),
    Bone("Face_Jowl", "Face_Jawbone"),
    Bone("Face_chopRight", "Face_Jawbone"),
    Bone("Face_chopLeft", "Face_Jawbone"),
    Bone("Face_LipLowerMiddle", "Face_Jawbone"),
    Bone("Face_LipLowerLeft", "Face_Jawbone"),
    Bone("Face_LipLowerRight", "Face_Jawbone"),
    Bone("Face_Chin", "Face_Jawbone"),
    Bone("Face_Tongue", "Face_Jawbone"),
    Bone("Face_CornerRight", "Face_Hub"),
    Bone("Face_CheekSideRight", "Face_CornerRight"),
    Bone("Face_CornerLeft", "Face_Hub"),
    Bone("Face_CheekSideLeft", "Face_CornerLeft"),
    Bone("Face_CheekFrontRight", "Face_Hub"),
    Bone("Face_CheekFrontLeft", "Face_Hub"),
    Bone("Face_CheekUpperRight", "Face_Hub"),
    Bone("Face_CheekUpperLeft", "Face_Hub"),
    Bone("Face_LipUpperMiddle", "Face_Hub"),
    Bone("Face_LipUpperRight", "Face_Hub"),
    Bone("Face_LipUpperLeft", "Face_Hub"),
    Bone("Face_NostrilRight", "Face_Hub"),
    Bone("Face_NostrilLeft", "Face_Hub"),
    Bone("Face_Forehead", "Face_Hub"),
    Bone("Face_BrowFrontRight", "Face_Forehead"),
    Bone("Face_BrowFrontLeft", "Face_Forehead"),
    Bone("Face_BrowMiddle", "Face_Forehead"),
    Bone("Face_BrowSideRight", "Face_Forehead"),
    Bone("Face_BrowSideLeft", "Face_Forehead"),
    Bone("Face_Eyelids", "Face_Hub"),
    Bone("Face_EyelidUpperRight", "Face_Hub"),
    Bone("Face_EyelidUpperLeft", "Face_Hub"),
    Bone("Face_EyelidLowerRight", "Face_Hub"),
    Bone("Face_EyelidLowerLeft", "Face_Hub"),
    Bone("EyeLeft", "Face_Hub"),
    Bone("EyeRight", "Face_Hub"),
    Bone("LeftShoulder", "Spine3"),
    Bone("LeftArm", "LeftShoulder"),
    Bone("LeftArmRoll", "LeftArm"),
    Bone("LeftForeArm", "LeftArmRoll"),
    Bone("LeftForeArmRoll", "LeftForeArm"),
    Bone("LeftHand", "LeftForeArmRoll"),
    Bone("LeftHandRing", "LeftHand"),
    Bone("LeftHandRing1", "LeftHandRing"),
    Bone("LeftHandRing2", "LeftHandRing1"),
    Bone("LeftHandRing3", "LeftHandRing2"),
    Bone("LeftHandPinky1", "LeftHandRing"),
    Bone("LeftHandPinky2", "LeftHandPinky1"),
    Bone("LeftHandPinky3", "LeftHandPinky2"),
    Bone("LeftHandMiddle1", "LeftHand"),
    Bone("LeftHandMiddle2", "LeftHandMiddle1"),
    Bone("LeftHandMiddle3", "LeftHandMiddle2"),
    Bone("LeftHandIndex1", "LeftHand"),
    Bone("LeftHandIndex2", "LeftHandIndex1"),
    Bone("LeftHandIndex3", "LeftHandIndex2"),
    Bone("LeftHandThumb1", "LeftHand"),
    Bone("LeftHandThumb2", "LeftHandThumb1"),
    Bone("LeftHandThumb3", "LeftHandThumb2"),
    Bone("RightShoulder", "Spine3"),
    Bone("RightArm", "RightShoulder"),
    Bone("RightArmRoll", "RightArm"),
    Bone("RightForeArm", "RightArmRoll"),
    Bone("RightForeArmRoll", "RightForeArm"),
    Bone("RightHand", "RightForeArmRoll"),
    Bone("RightHandRing", "RightHand"),
    Bone("RightHandRing1", "RightHandRing"),
    Bone("RightHandRing2", "RightHandRing1"),
    Bone("RightHandRing3", "RightHandRing2"),
    Bone("RightHandPinky1", "RightHandRing"),
    Bone("RightHandPinky2", "RightHandPinky1"),
    Bone("RightHandPinky3", "RightHandPinky2"),
    Bone("RightHandMiddle1", "RightHand"),
    Bone("RightHandMiddle2", "RightHandMiddle1"),
    Bone("RightHandMiddle3", "RightHandMiddle2"),
    Bone("RightHandIndex1", "RightHand"),
    Bone("RightHandIndex2", "RightHandIndex1"),
    Bone("RightHandIndex3", "RightHandIndex2"),
    Bone("RightHandThumb1", "RightHand"),
    Bone("RightHandThumb2", "RightHandThumb1"),
    Bone("RightHandThumb3", "RightHandThumb2"),
    Bone("LeftUpLeg", "Pelvis"),
    Bone("LeftUpLegRoll", "LeftUpLeg"),
    Bone("LeftLeg", "LeftUpLegRoll"),
    Bone("LeftLegRoll", "LeftLeg"),
    Bone("LeftFoot", "LeftLegRoll"),
    Bone("LeftToeBase", "LeftFoot"),
    Bone("RightUpLeg", "Pelvis"),
    Bone("RightUpLegRoll", "RightUpLeg"),
    Bone("RightLeg", "RightUpLegRoll"),
    Bone("RightLegRoll", "RightLeg"),
    Bone("RightFoot", "RightLegRoll"),
    Bone("RightToeBase", "RightFoot")
)
"""Default Arma 3 character skeleton structure."""


OFP2_MANSKELETON_LOWERCASE: BoneSequence = tuple(
    [
        Bone(b.name.lower(), b.parent.lower())
        for b in OFP2_MANSKELETON
    ]
)
"""Default Arma 3 character skeleton structure with all lowercase names."""
