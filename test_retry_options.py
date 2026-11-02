from unittest.mock import MagicMock
import pytest
import script

@pytest.mark.parametrize('retries', [0, -1, 1.5, True, '3', None])
def test_invalid_retry_count_does_not_open_session(monkeypatch, retries):
    constructor = MagicMock()
    monkeypatch.setattr(script.requests, 'Session', constructor)
    with pytest.raises(ValueError, match='retries'):
        script.StealthSession(retries=retries)
    constructor.assert_not_called()
