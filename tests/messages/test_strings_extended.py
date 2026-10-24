"""Extended tests for mido.messages.strings (msg2str / str2msg)."""

import pytest

from mido import Message
from mido.messages.strings import msg2str, str2msg


def test_msg2str_includes_attributes_and_time():
    msg = Message('note_on', channel=0, note=60, velocity=64, time=5)
    assert msg2str(msg.dict()) == 'note_on channel=0 note=60 velocity=64 time=5'


def test_msg2str_without_time():
    msg = Message('note_on', channel=0, note=60, velocity=64, time=5)
    assert msg2str(msg.dict(), include_time=False) == \
        'note_on channel=0 note=60 velocity=64'


def test_msg2str_sysex_data_in_parentheses():
    msg = Message('sysex', data=[1, 2, 3])
    assert msg2str(msg.dict()) == 'sysex data=(1,2,3) time=0'


def test_str2msg_roundtrip():
    for text in ['note_on channel=0 note=60 velocity=64 time=5',
                 'sysex data=(1,2,3) time=0',
                 'clock time=0']:
        msgdict = str2msg(text)
        assert msg2str(msgdict) == text


def test_str2msg_float_time_stays_float():
    msgdict = str2msg('note_on note=60 velocity=64 time=0.5')
    assert msgdict['time'] == 0.5
    assert isinstance(msgdict['time'], float)


def test_str2msg_int_time_stays_int():
    msgdict = str2msg('clock time=3')
    assert msgdict['time'] == 3
    assert isinstance(msgdict['time'], int)


def test_str2msg_empty_sysex_data():
    assert str2msg('sysex data=()')['data'] == []


def test_str2msg_data_without_parentheses():
    with pytest.raises(ValueError):
        str2msg('sysex data=1,2')


def test_str2msg_data_non_numeric():
    with pytest.raises(ValueError):
        str2msg('sysex data=(a,b)')


def test_str2msg_invalid_time():
    with pytest.raises(ValueError):
        str2msg('note_on note=60 time=abc')


def test_str2msg_fills_in_defaults():
    msgdict = str2msg('note_on note=60')
    assert msgdict == {'type': 'note_on', 'time': 0, 'channel': 0,
                       'note': 60, 'velocity': 64}
