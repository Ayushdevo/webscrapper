from unittest.mock import MagicMock
import pytest
import script

@pytest.mark.parametrize('stage', ['new_context', 'goto', 'content'])
def test_browser_closes_after_failure(monkeypatch, stage):
    playwright = MagicMock()
    monkeypatch.setattr(script, 'PLAYWRIGHT_OK', True)
    monkeypatch.setattr(script, 'sync_playwright', playwright, raising=False)
    browser = playwright.return_value.__enter__.return_value.chromium.launch.return_value
    target = browser if stage == 'new_context' else browser.new_context.return_value.new_page.return_value
    getattr(target, stage).side_effect = RuntimeError(stage)
    with pytest.raises(RuntimeError, match=stage):
        script.fetch_with_playwright('https://example.com')
    browser.close.assert_called_once()
