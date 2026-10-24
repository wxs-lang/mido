"""Structural tests for mido.MidiFile: defaults, header bytes written
by save(), load round trips, iteration and the length property.
"""

import io

import pytest

from mido import Message, MetaMessage, MidiFile, MidiTrack


def _make_file(ticks_per_beat=480, tempo=None, note_ticks=480):
    mid = MidiFile(ticks_per_beat=ticks_per_beat)
    track = mid.add_track('Lead')
    if tempo is not None:
        track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    track.append(Message('note_on', note=60, velocity=64, time=0))
    track.append(Message('note_off', note=60, velocity=64, time=note_ticks))
    track.append(MetaMessage('end_of_track', time=0))
    return mid


def test_defaults():
    mid = MidiFile()
    assert mid.type == 1
    assert mid.ticks_per_beat == 480
    assert mid.charset == 'latin1'
    assert mid.tracks == []


def test_invalid_type():
    # The error message itself is garbled upstream (it interpolates the
    # builtin `format`), so only the exception type is pinned here.
    with pytest.raises(ValueError):
        MidiFile(type=3)


def test_add_track_with_and_without_name():
    mid = MidiFile()
    named = mid.add_track('Lead')
    assert isinstance(named, MidiTrack)
    assert named.name == 'Lead'
    assert named[0] == MetaMessage('track_name', name='Lead', time=0)

    unnamed = mid.add_track()
    assert len(unnamed) == 0
    assert len(mid.tracks) == 2


def test_save_writes_header_chunk():
    data = io.BytesIO()
    _make_file().save(file=data)
    raw = data.getvalue()
    # 'MThd', chunk size 6, format 1, 1 track, 480 ticks per beat.
    assert raw[:14] == b'MThd\x00\x00\x00\x06\x00\x01\x00\x01\x01\xe0'
    assert raw[14:18] == b'MTrk'


def test_save_load_roundtrip():
    mid = _make_file()
    data = io.BytesIO()
    mid.save(file=data)
    data.seek(0)

    loaded = MidiFile(file=data)
    assert loaded.type == 1
    assert loaded.ticks_per_beat == 480
    assert len(loaded.tracks) == 1
    assert list(loaded.tracks[0]) == list(mid.tracks[0])


def test_iteration_yields_all_tracks_messages_in_order():
    mid = _make_file()
    assert [m.type for m in mid] == [
        'track_name', 'note_on', 'note_off', 'end_of_track',
    ]


def test_merged_track_property():
    mid = _make_file()
    assert [m.type for m in mid.merged_track] == [
        'track_name', 'note_on', 'note_off', 'end_of_track',
    ]


def test_length_uses_default_tempo():
    # 480 ticks at 480 ticks/beat and the default tempo of 500000 us
    # per beat is exactly half a second.
    assert _make_file().length == 0.5


def test_length_uses_tempo_from_file():
    # 96 ticks at 96 ticks/beat = 1 beat; at 250000 us/beat = 0.25 s.
    mid = _make_file(ticks_per_beat=96, tempo=250000, note_ticks=96)
    assert mid.length == 0.25
