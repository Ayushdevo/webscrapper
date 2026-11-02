from unittest.mock import MagicMock
import script

def test_rate_limited_response_is_closed_before_next_attempt(monkeypatch):
    session = script.StealthSession(retries=2)
    first, second = MagicMock(), MagicMock()
    first.status_code = 429
    first.raise_for_status.side_effect = script.requests.HTTPError('rate limited')
    second.status_code = 200
    second.content = b'ok'
    events = []
    first.close.side_effect = lambda: events.append('closed')
    def get(*args, **kwargs):
        if events:
            assert events == ['closed']
            return second
        events.append('first')
        return first
    # Use a separate invocation counter so a missing close cannot hide the retry.
    calls = iter([first, second])
    def fetch(*args, **kwargs):
        response = next(calls)
        if response is second:
            assert events == ['closed']
        return response
    monkeypatch.setattr(session.session, 'get', fetch)
    monkeypatch.setattr(script.time, 'sleep', lambda _: None)
    try:
        assert session.get('https://example.com') is second
        first.close.assert_called_once()
        second.close.assert_not_called()
    finally:
        session.close()
