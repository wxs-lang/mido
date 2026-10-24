"""Small, deterministic tests for mido.merge_tracks.

The existing suite only merges one large file. These tests pin the
ordering, delta-time recomputation and end_of_track handling on
minimal examples.
"""

from mido import Message, MetaMessage, MidiTrack, merge_tracks


def _note_track(notes):
    return MidiTrack(notes)


def test_merge_interleaves_by_absolute_time():
    track1 = _note_track([
        Message('note_on', note=60, velocity=64, time=0),
        Message('note_off', note=60, velocity=64, time=100),
        MetaMessage('end_of_track', time=0),
    ])
    track2 = _note_track([
        Message('note_on', note=62, velocity=64, time=50),
        Message('note_off', note=62, velocity=64, time=60),
        MetaMessage('end_of_track', time=0),
    ])

    merged = merge_tracks([track1, track2])

    assert isinstance(merged, MidiTrack)
    assert [(m.type, getattr(m, 'note', None), m.time) for m in merged] == [
        ('note_on', 60, 0),
        ('note_on', 62, 50),
        ('note_off', 60, 50),
        ('note_off', 62, 10),
        ('end_of_track', None, 0),
    ]


def test_merge_keeps_both_track_names_in_order():
    track_a = MidiTrack([
        MetaMessage('track_name', name='A', time=0),
        Message('note_on', note=1, time=10),
        MetaMessage('end_of_track', time=5),
    ])
    track_b = MidiTrack([
        MetaMessage('track_name', name='B', time=0),
        Message('note_on', note=2, time=0),
        MetaMessage('end_of_track', time=0),
    ])

    merged = merge_tracks([track_a, track_b])

    assert [repr(m) for m in merged] == [
        repr(MetaMessage('track_name', name='A', time=0)),
        repr(MetaMessage('track_name', name='B', time=0)),
        repr(Message('note_on', note=2, time=0)),
        repr(Message('note_on', note=1, time=10)),
        repr(MetaMessage('end_of_track', time=5)),
    ]


def test_merge_no_tracks_gives_single_end_of_track():
    merged = merge_tracks([])
    assert list(merged) == [MetaMessage('end_of_track', time=0)]


def test_merge_result_has_exactly_one_end_of_track():
    track = MidiTrack([
        Message('note_on', note=60, time=0),
        MetaMessage('end_of_track', time=0),
    ])
    merged = merge_tracks([track, track.copy()])
    assert [m.type for m in merged].count('end_of_track') == 1
    assert merged[-1].type == 'end_of_track'
