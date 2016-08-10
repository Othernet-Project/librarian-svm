import mock
import pytest

import librarian_svm.svm as mod


@pytest.mark.parametrize('v1,v2,correct', [
    ('0.2', '0.1', False),
    ('0.1', '0.2', True),
    ('0.1.002b4', '0.1.002b5', True),
    ('0.2.004a3', '0.2.003b8', False),
    ('1.2rc1', '1.3', True),
    ('1.0', '1.0rc1', False),
    ('0.7', '0.7b', False),
    ('0.1.4a5', '0.1.4rc2', True),
])
def test_comparisons(v1, v2, correct):
    pattern = '/boot/overlay-name-{}.sqfs'
    o1 = mod.Overlay(pattern.format(v1))
    o2 = mod.Overlay(pattern.format(v2))
    assert (o1 < o2) is correct
    assert (o1 > o2) is not correct
    assert o1 != o2
    assert not (o1 == o2)
