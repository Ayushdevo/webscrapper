from unittest.mock import MagicMock
import pytest
import script

@pytest.mark.parametrize('status', [404, 500])
def test_browser_rejects_error_documents(monkeypatch, status):
    playwright = MagicMock()
    monkeypatch.setattr(script, 'PLAYWRIGHT_OK', True)
    monkeypatch.setattr(script, 'sync_playwright', playwright, raising=False)
    browser = playwright.return_value.__enter__.return_value.chromium.launch.return_value
    page = browser.new_context.return_value.new_page.return_value
    page.goto.return_value.ok = False
    page.goto.return_value.status = status
    with pytest.raises(RuntimeError, match=str(status)):
        script.fetch_with_playwright('https://example.com')
    page.content.assert_not_called()
    browser.close.assert_called_once()
