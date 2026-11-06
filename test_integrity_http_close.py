from unittest.mock import MagicMock
import pytest
import script

@pytest.mark.parametrize('status,retries', [(404, 3), (429, 1), (500, 3)])
def test_failed_response_closed(monkeypatch, status, retries):
    response = MagicMock(status_code=status)
    response.raise_for_status.side_effect = script.requests.HTTPError('failure')
    session = script.StealthSession(retries=retries)
    monkeypatch.setattr(session.session, 'get', lambda *a, **k: response)
    monkeypatch.setattr(script.time, 'sleep', lambda _: None)
    try:
        with pytest.raises(script.requests.HTTPError):
            session.get('https://example.com')
        response.close.assert_called_once()
    finally:
        session.close()
