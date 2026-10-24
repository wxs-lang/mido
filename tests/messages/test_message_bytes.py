"""Byte-level round trips for every message type in the spec table.

Each message is encoded with .bytes() and decoded with
Message.from_bytes(); both the exact wire bytes and the round-trip
equality are pinned.
"""

import pytest

from mido import Message

CASES = [
    (Message('note_on', channel=3, note=60, velocity=64), [147, 60, 64]),
    (Message('note_off', channel=0, note=60, velocity=0), [128, 60, 0]),
    (Message('control_change', channel=9, control=7, value=100), [185, 7, 100]),
    (Message('program_change', channel=1, program=10), [193, 10]),
    (Message('pitchwheel', channel=0, pitch=-8192), [224, 0, 0]),
    (Message('pitchwheel', channel=0, pitch=8191), [224, 127, 127]),
    (Message('pitchwheel', channel=0, pitch=0), [224, 0, 64]),
    (Message('aftertouch', channel=2, value=90), [210, 90]),
    (Message('polytouch', channel=2, note=61, value=90), [162, 61, 90]),
    (Message('sysex', data=[0x41, 0x10, 0x42]), [240, 65, 16, 66, 247]),
    (Message('sysex', data=[]), [240, 247]),
    (Message('quarter_frame', frame_type=3, frame_value=9), [241, 57]),
    (Message('quarter_frame', frame_type=7, frame_value=15), [241, 127]),
    (Message('songpos', pos=1024), [242, 0, 8]),
    (Message('songpos', pos=16383), [242, 127, 127]),
    (Message('songpos', pos=0), [242, 0, 0]),
    (Message('song_select', song=5), [243, 5]),
    (Message('tune_request'), [246]),
    (Message('clock'), [248]),
    (Message('start'), [250]),
    (Message('continue'), [251]),
    (Message('stop'), [252]),
    (Message('active_sensing'), [254]),
    (Message('reset'), [255]),
]


@pytest.mark.parametrize("msg,wire", CASES, ids=[c[0].type + str(i) for i, c in enumerate(CASES)])
def test_bytes_and_roundtrip(msg, wire):
    assert msg.bytes() == wire
    assert Message.from_bytes(wire) == msg
    assert Message.from_bytes(bytes(wire)) == msg


def test_hex_roundtrip():
    msg = Message('note_on', note=60, velocity=64)
    assert msg.hex() == '90 3C 40'
    assert Message.from_hex('90 3C 40') == msg
    assert Message.from_hex('903c40') == msg


def test_hex_invalid():
    with pytest.raises(ValueError):
        Message.from_hex('zz')


def test_dict_defaults_and_sysex_data():
    assert Message('note_on').dict() == {
        'type': 'note_on', 'time': 0, 'channel': 0, 'note': 0, 'velocity': 64,
    }
    # dict() exposes sysex data as a plain list, not the internal wrapper.
    assert Message('sysex', data=[1, 2]).dict()['data'] == [1, 2]
