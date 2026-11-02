from unittest.mock import MagicMock
import requests
import script

def test_requests_redirect_sets_link_base_and_classification(monkeypatch, tmp_path):
    response = requests.Response()
    response.status_code = 200
    response.url = 'https://other.example/articles/page'
    response._content = b'<a href="next">Next</a>'
    session = MagicMock()
    session.get.return_value = response
    monkeypatch.setattr(script, 'StealthSession', lambda **kw: session)
    result = script.DataPulseScraper(output_dir=tmp_path).scrape('https://example.com/start', mode='links')
    assert result['data']['links'] == [{'href':'https://other.example/articles/next', 'text':'Next', 'type':'internal', 'rel':''}]

def test_browser_redirect_sets_link_base(monkeypatch, tmp_path):
    playwright = MagicMock()
    monkeypatch.setattr(script, 'PLAYWRIGHT_OK', True)
    monkeypatch.setattr(script, 'sync_playwright', playwright, raising=False)
    page = playwright.return_value.__enter__.return_value.chromium.launch.return_value.new_context.return_value.new_page.return_value
    page.url = 'https://other.example/dir/page'
    page.content.return_value = '<a href="next">Next</a>'
    result = script.DataPulseScraper(use_playwright=True, output_dir=tmp_path).scrape('https://example.com', mode='links')
    assert result['data']['links'][0]['href'] == 'https://other.example/dir/next'
