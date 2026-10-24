"""Extended tests for mido.messages.checks.

The existing test_checks.py only covers check_time. These tests pin the
range and type behaviour of every other registered check, both directly
through check_value() and through Message construction.
"""

import pytest

from mido import Message
from mido.messages.checks import check_msgdict, check_value


@pytest.mark.parametrize("value", [0, 1, 15])
def test_channel_valid(value):
    check_value('channel', value)


@pytest.mark.parametrize("value,exc", [
    (16, ValueError),
    (-1, ValueError),
    (1.5, TypeError),
    ('0', TypeError),
])
def test_channel_invalid(value, exc):
    with pytest.raises(exc):
        check_value('channel', value)


@pytest.mark.parametrize("name", ['note', 'velocity', 'control', 'value',
                                  'program', 'song'])
@pytest.mark.parametrize("value", [0, 64, 127])
def test_data_byte_attributes_valid(name, value):
    check_value(name, value)


@pytest.mark.parametrize("name", ['note', 'velocity', 'control', 'program'])
@pytest.mark.parametrize("value,exc", [
    (128, ValueError),
    (-1, ValueError),
    (64.0, TypeError),
])
def test_data_byte_attributes_invalid(name, value, exc):
    with pytest.raises(exc):
        check_value(name, value)


@pytest.mark.parametrize("value", [-8192, 0, 8191])
def test_pitch_valid(value):
    check_value('pitch', value)


@pytest.mark.parametrize("value,exc", [
    (8192, ValueError),
    (-8193, ValueError),
    (0.5, TypeError),
])
def test_pitch_invalid(value, exc):
    with pytest.raises(exc):
        check_value('pitch', value)


@pytest.mark.parametrize("value", [0, 8192, 16383])
def test_pos_valid(value):
    check_value('pos', value)


@pytest.mark.parametrize("value,exc", [
    (16384, ValueError),
    (-1, ValueError),
    ('x', TypeError),
])
def test_pos_invalid(value, exc):
    with pytest.raises(exc):
        check_value('pos', value)


def test_frame_type_and_value_ranges():
    check_value('frame_type', 0)
    check_value('frame_type', 7)
    check_value('frame_value', 0)
    check_value('frame_value', 15)
    with pytest.raises(ValueError):
        check_value('frame_type', 8)
    with pytest.raises(ValueError):
        check_value('frame_value', 16)
    with pytest.raises(TypeError):
        check_value('frame_type', 1.5)


def test_data_check():
    check_value('data', [])
    check_value('data', [0, 65, 127])
    with pytest.raises(ValueError):
        check_value('data', [0, 128])
    with pytest.raises(TypeError):
        check_value('data', ['a'])


def test_type_check():
    check_value('type', 'note_on')
    check_value('type', 'sysex')
    with pytest.raises(ValueError):
        check_value('type', 'bogus_type')


def test_time_check_accepts_int_and_float_only():
    check_value('time', 0)
    check_value('time', 0.5)
    with pytest.raises(TypeError):
        check_value('time', '0.5')


def test_check_msgdict_valid():
    assert check_msgdict({'type': 'note_on', 'channel': 0,
                          'note': 60, 'velocity': 64}) is None


def test_check_msgdict_unknown_type():
    with pytest.raises(ValueError):
        check_msgdict({'type': 'bogus_type'})


def test_check_msgdict_unknown_attribute():
    with pytest.raises(ValueError):
        check_msgdict({'type': 'note_on', 'bogus': 1})


def test_check_msgdict_bad_value():
    with pytest.raises(ValueError):
        check_msgdict({'type': 'note_on', 'note': 200})


def test_message_construction_enforces_checks():
    with pytest.raises(ValueError):
        Message('note_on', channel=16)
    with pytest.raises(TypeError):
        Message('note_on', channel=1.5)
    with pytest.raises(ValueError):
        Message('pitchwheel', pitch=8192)
    with pytest.raises(ValueError):
        Message('songpos', pos=16384)
    with pytest.raises(ValueError):
        Message('quarter_frame', frame_type=8)
    with pytest.raises(TypeError):
        Message('note_on', time='soon')
    # Float time is fine.
    assert Message('note_on', time=0.5).time == 0.5
