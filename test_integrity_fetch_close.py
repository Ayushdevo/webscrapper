from unittest.mock import MagicMock
import pytest
import script

@pytest.mark.parametrize('broken', [False, True])
def test_fetch_closes_response_even_when_decoding_fails(monkeypatch, tmp_path, broken):
    response = MagicMock(content=b'<p>hello</p>', url='https://example.com', headers={})
    session = MagicMock()
    session.get.return_value = response
    monkeypatch.setattr(script, 'StealthSession', lambda **kw: session)
    if broken:
        monkeypatch.setattr(script, 'UnicodeDammit', MagicMock(side_effect=ValueError('decode')))
    scraper = script.DataPulseScraper(output_dir=str(tmp_path))
    if broken:
        with pytest.raises(ValueError, match='decode'):
            scraper.fetch_html('https://example.com')
    else:
        assert 'hello' in scraper.fetch_html('https://example.com')
    response.close.assert_called_once()
    session.close.assert_called_once()
