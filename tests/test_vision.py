import numpy as np

from autoclicker.vision import find, load_template, save_template


def make_screen(seed=0):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, (300, 400, 3), dtype=np.uint8)


def make_template(seed=1):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, (20, 60, 3), dtype=np.uint8)


def test_finds_center_of_template():
    screen = make_screen()
    template = make_template()
    screen[100:120, 250:310] = template
    assert find(template, screen) == (280, 110)


def test_returns_none_when_absent():
    assert find(make_template(), make_screen()) is None


def test_returns_none_when_template_bigger_than_screen():
    assert find(make_screen(), make_template()) is None


def test_template_roundtrip(tmp_path):
    path = tmp_path / "образец" / "template.png"
    template = make_template()
    save_template(template, path)
    assert np.array_equal(load_template(path), template)


def test_load_missing_template(tmp_path):
    assert load_template(tmp_path / "nope.png") is None
