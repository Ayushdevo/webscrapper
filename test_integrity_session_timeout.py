import pytest
import script

@pytest.mark.parametrize('timeout', [True, False, 0, -1, float('inf'), float('nan'), '20', None, 10**1000])
def test_session_rejects_invalid_timeout(timeout):
    with pytest.raises(ValueError, match='timeout'):
        script.StealthSession(timeout=timeout)

def test_session_accepts_fractional_timeout():
    session = script.StealthSession(timeout=0.25)
    try:
        assert session.timeout == 0.25
    finally:
        session.close()
