from io import BytesIO

from pytest import approx, raises

from armaio.rtm import (
    RtmMatrix,
    RtmError,
    RtmFile,
    RtmFrame,
    BmtrFile
)


mat: RtmMatrix = (
    (1.0, 1.0, 1.0, 1.0),
    (1.0, 1.0, 1.0, 1.0),
    (1.0, 1.0, 1.0, 1.0),
    (1.0, 1.0, 1.0, 1.0)
)


def test_rtm_reading() -> None:
    rtm = RtmFile.read_file("tests/data/animation.rtm")
    assert len(rtm.properties) == 2
    assert len(rtm.frames) == 2
    assert rtm.bones is not None
    assert len(rtm.bones) == 4
    assert rtm.motion == approx((1.0, 3.0, 2.0))


def test_rtm_creation() -> None:
    rtm = RtmFile()

    rtm.add_property(0.0, "prop1", "value1")
    rtm.add_property(1.0, "prop2", "value2")
    assert len(rtm.properties) == 2

    prop = rtm.pop_property(0)
    assert prop.name == "prop1"
    assert len(rtm.properties) == 1

    frame0 = RtmFrame(0.0, ("bone1", "bone2"))
    assert len(frame0.transforms) == 2
    frame0.set_transform("bone1", mat)
    with raises(ValueError):
        frame0.set_transform("bone3", mat)

    rtm.add_frame(frame0)
    assert rtm.bones == ("bone1", "bone2")

    frame1 = RtmFrame(0.1, ("bone1", "bone2", "bone3"))
    with raises(ValueError):
        rtm.add_frame(frame1)

    rtm.motion = (1.0, 2.0, 3.0)
    assert rtm.motion == approx((1.0, 2.0, 3.0))

    with BytesIO() as stream:
        rtm.write(stream)
        raw = stream.getvalue()

    assert len(raw) > 0

    rtm.pop_frame(0)
    assert len(rtm.frames) == 0
    assert rtm.bones is None

    with raises(RtmError):
        rtm.write(BytesIO())


def test_bmtr_reading() -> None:
    bmtr = BmtrFile.read_file("tests/data/animation_bmtr.rtm")
    assert len(bmtr.properties) == 0
    assert len(bmtr.frames) == 165
    assert bmtr.bones is not None
    assert len(bmtr.bones) == 66
    assert bmtr.motion == approx((0.0, 0.0, 0.0))

    frame0 = bmtr.frames[0]
    transform = frame0.transforms["pelvis"]
    assert transform is not None
