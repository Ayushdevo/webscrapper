from unittest.mock import MagicMock
import pytest
import requests
import script

@pytest.mark.parametrize('encoding,text', [('utf-8','नमस्ते'), ('windows-1252','café')])
def test_meta_charset_overrides_http_html_default(monkeypatch, tmp_path, encoding, text):
    response = requests.Response()
    response.status_code = 200
    response.headers['Content-Type'] = 'text/html'
    response.encoding = 'ISO-8859-1'
    response._content = ('<meta charset="' + encoding + '"><p>' + text + '</p>').encode(encoding)
    session = MagicMock()
    session.get.return_value = response
    monkeypatch.setattr(script, 'StealthSession', lambda **kw: session)
    result = script.DataPulseScraper(output_dir=tmp_path).fetch_html('https://example.com')
    assert text in result
    session.close.assert_called_once()

def test_explicit_http_charset_is_preserved(monkeypatch, tmp_path):
    response = requests.Response()
    response.status_code = 200
    response.headers['Content-Type'] = 'text/html; charset=windows-1252'
    response.encoding = 'windows-1252'
    response._content = b'<meta charset="utf-8"><p>caf\xe9</p>'
    session = MagicMock()
    session.get.return_value = response
    monkeypatch.setattr(script, 'StealthSession', lambda **kw: session)
    assert 'café' in script.DataPulseScraper(output_dir=tmp_path).fetch_html('https://example.com')
