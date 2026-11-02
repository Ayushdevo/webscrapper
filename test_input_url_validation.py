from unittest.mock import MagicMock
import pytest
import script

@pytest.mark.parametrize('url', ['https://:443/path', 'http://example.com:bad/', 'http://example.com:99999/', 'https://exa mple.com/'])
def test_invalid_target_never_reaches_fetch(monkeypatch, tmp_path, url):
    scraper = script.DataPulseScraper(output_dir=tmp_path)
    fetch = MagicMock()
    monkeypatch.setattr(scraper, 'fetch_html', fetch)
    with pytest.raises(ValueError, match='HTTP or HTTPS URL'):
        scraper.scrape(url)
    fetch.assert_not_called()
