"""Extended tests for mido.midifiles.meta.

The existing test_meta.py covers copy semantics, key signatures from
bytes and a few error paths. These tests pin the wire encoding of the
common meta message types, their validation ranges, from_bytes()
round trips, unknown meta messages and variable-length integers.
"""

import pytest

from mido import MetaMessage
from mido.midifiles.meta import (
    UnknownMetaMessage,
    decode_variable_int,
    encode_variable_int,
)

BUILD_CASES = [
    (MetaMessage('set_tempo', tempo=500000), [255, 81, 3, 7, 161, 32]),
    (MetaMessage('set_tempo', tempo=0), [255, 81, 3, 0, 0, 0]),
    (MetaMessage('set_tempo', tempo=16777215), [255, 81, 3, 255, 255, 255]),
    (MetaMessage('text', text='hello'), [255, 1, 5, 104, 101, 108, 108, 111]),
    (MetaMessage('track_name', name='Piano'), [255, 3, 5, 80, 105, 97, 110, 111]),
    (MetaMessage('device_name', name='dev'), [255, 9, 3, 100, 101, 118]),
    (MetaMessage('lyrics', text='la'), [255, 5, 2, 108, 97]),
    (MetaMessage('marker', text='chorus'), [255, 6, 6, 99, 104, 111, 114, 117, 115]),
    (MetaMessage('time_signature', numerator=3, denominator=4),
     [255, 88, 4, 3, 2, 24, 8]),
    # Defaults: 4/4, 24 clocks per click, 8 notated 32nd notes per beat.
    (MetaMessage('time_signature'), [255, 88, 4, 4, 2, 24, 8]),
    (MetaMessage('time_signature', numerator=6, denominator=8),
     [255, 88, 4, 6, 3, 24, 8]),
    (MetaMessage('key_signature', key='G'), [255, 89, 2, 1, 0]),
    (MetaMessage('key_signature', key='Am'), [255, 89, 2, 0, 1]),
    (MetaMessage('key_signature', key='Eb'), [255, 89, 2, 253, 0]),
    (MetaMessage('key_signature', key='C'), [255, 89, 2, 0, 0]),
    (MetaMessage('channel_prefix', channel=5), [255, 32, 1, 5]),
    (MetaMessage('midi_port', port=2), [255, 33, 1, 2]),
    (MetaMessage('sequence_number', number=300), [255, 0, 2, 1, 44]),
    (MetaMessage('sequence_number', number=0), [255, 0, 2, 0, 0]),
    (MetaMessage('sequencer_specific', data=[1, 2, 3]), [255, 127, 3, 1, 2, 3]),
    (MetaMessage('end_of_track'), [255, 47, 0]),
]


@pytest.mark.parametrize("msg,wire", BUILD_CASES,
                         ids=[c[0].type + str(i) for i, c in enumerate(BUILD_CASES)])
def test_meta_wire_bytes(msg, wire):
    assert msg.bytes() == wire


ROUNDTRIP_CASES = [c for c in BUILD_CASES if c[0].type != 'sequencer_specific']


@pytest.mark.parametrize("msg,wire", ROUNDTRIP_CASES,
                         ids=[c[0].type + str(i) for i, c in enumerate(ROUNDTRIP_CASES)])
def test_meta_from_bytes_roundtrip(msg, wire):
    assert MetaMessage.from_bytes(wire) == msg


def test_sequencer_specific_from_bytes_data_is_tuple():
    # Quirk: unlike the other data-carrying messages, a decoded
    # sequencer_specific message exposes its data as a tuple, so it does
    # not compare equal to one constructed with a list. Pinned as
    # current behaviour.
    decoded = MetaMessage.from_bytes([255, 127, 3, 1, 2, 3])
    assert decoded.data == (1, 2, 3)
    assert isinstance(decoded.data, tuple)
    assert decoded.bytes() == [255, 127, 3, 1, 2, 3]


@pytest.mark.parametrize("fr,first_byte", [(24, 0), (25, 32), (29.97, 64), (30, 96)])
def test_smpte_offset_frame_rate_codes(fr, first_byte):
    msg = MetaMessage('smpte_offset', frame_rate=fr, hours=1, minutes=2,
                      seconds=3, frames=4, sub_frames=5)
    # The frame rate code occupies the top 3 bits of the hours byte.
    assert msg.bytes() == [255, 84, 5, first_byte + 1, 2, 3, 4, 5]


def test_smpte_offset_invalid_frame_rate_int():
    # Known quirk: an int frame rate other than 24/25/30 fails with a
    # misleading TypeError from inside the encoder (29.97 must be used
    # for drop-frame). Pinned as current behaviour.
    with pytest.raises(TypeError):
        MetaMessage('smpte_offset', frame_rate=29)


def test_set_tempo_range():
    with pytest.raises(ValueError):
        MetaMessage('set_tempo', tempo=-1)
    with pytest.raises(ValueError):
        MetaMessage('set_tempo', tempo=16777216)


def test_sequence_number_range():
    assert MetaMessage('sequence_number', number=65535).number == 65535
    with pytest.raises(ValueError):
        MetaMessage('sequence_number', number=65536)


def test_key_signature_invalid_key():
    with pytest.raises(ValueError):
        MetaMessage('key_signature', key='H')


def test_channel_prefix_and_port_accept_full_byte_range():
    # Unlike channel messages, these are checked as 0..255 bytes.
    assert MetaMessage('channel_prefix', channel=16).bytes() == [255, 32, 1, 16]
    assert MetaMessage('midi_port', port=128).bytes() == [255, 33, 1, 128]


def test_unknown_meta_message():
    msg = UnknownMetaMessage(0x66, [1, 2, 3])
    assert msg.type_byte == 0x66
    assert msg.bytes() == [255, 102, 3, 1, 2, 3]
    assert MetaMessage.from_bytes(msg.bytes()) == msg


@pytest.mark.parametrize("value,wire", [
    (0, [0]),
    (127, [127]),
    (128, [129, 0]),
    (255, [129, 127]),
    (8192, [192, 0]),
    (16383, [255, 127]),
    (16384, [129, 128, 0]),
    (0x0FFFFFFF, [255, 255, 255, 127]),
])
def test_encode_variable_int(value, wire):
    assert encode_variable_int(value) == wire
    assert decode_variable_int(wire) == value


def test_encode_variable_int_negative():
    with pytest.raises(ValueError):
        encode_variable_int(-1)


def test_encode_variable_int_beyond_four_bytes():
    # Known quirk: values above the MIDI spec maximum of 0x0FFFFFFF are
    # encoded as 5+ bytes instead of being rejected. Pinned as current
    # behaviour.
    assert encode_variable_int(0x10000000) == [129, 128, 128, 128, 0]
