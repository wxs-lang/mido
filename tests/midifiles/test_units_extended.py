"""Edge-case tests for mido.midifiles.units.

The existing test_units.py covers the main tempo/BPM conversions and
notes its tick/second tests "could be improved with better test values
such as edge cases" -- these are those edge cases.
"""

import pytest

from mido.midifiles.units import bpm2tempo, second2tick, tempo2bpm, tick2second


def test_tick2second_zero():
    assert tick2second(0, ticks_per_beat=480, tempo=500000) == 0.0


def test_tick2second_scales_with_tempo_and_resolution():
    assert tick2second(480, ticks_per_beat=480, tempo=500000) == 0.5
    assert tick2second(960, ticks_per_beat=480, tempo=250000) == 0.5
    assert tick2second(240, ticks_per_beat=480, tempo=500000) == 0.25
    assert tick2second(1, ticks_per_beat=96, tempo=500000) == pytest.approx(0.0052083333)


def test_second2tick_rounding():
    assert second2tick(0, ticks_per_beat=480, tempo=500000) == 0
    assert second2tick(0.5, ticks_per_beat=480, tempo=500000) == 480
    assert second2tick(1.0, ticks_per_beat=96, tempo=500000) == 192
    # 0.001 s is 0.96 ticks at the default scale, which rounds to 1.
    assert second2tick(0.001, ticks_per_beat=480, tempo=500000) == 1


def test_tick_second_roundtrip():
    for tick in [0, 1, 96, 480, 12345]:
        seconds = tick2second(tick, ticks_per_beat=480, tempo=500000)
        assert second2tick(seconds, ticks_per_beat=480, tempo=500000) == tick


def test_tempo_bpm_roundtrip():
    for tempo in [250000, 400000, 500000, 1000000]:
        assert bpm2tempo(tempo2bpm(tempo)) == tempo


def test_tempo2bpm_returns_float_for_uneven_tempos():
    assert tempo2bpm(333333) == pytest.approx(180.00018)
    assert isinstance(tempo2bpm(500000), float)


def test_bpm2tempo_rounds_to_int():
    assert bpm2tempo(120) == 500000
    assert bpm2tempo(60) == 1000000
    assert isinstance(bpm2tempo(121), int)
