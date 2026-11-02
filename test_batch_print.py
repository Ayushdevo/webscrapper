import json
from unittest.mock import MagicMock
import script

def test_batch_print_data(monkeypatch, tmp_path, capsys):
    batch = tmp_path / 'urls.txt'
    batch.write_text('https://example.com')
    fake = MagicMock()
    fake.batch_scrape.return_value = [{'url':'https://example.com', 'data': {'title':'नमस्ते'}}]
    monkeypatch.setattr(script, 'DataPulseScraper', lambda **kw: fake)
    monkeypatch.setattr(script, 'banner', lambda: None)
    monkeypatch.setattr(script, 'log', lambda *a: None)
    monkeypatch.setattr('sys.argv', ['script.py', '--batch', str(batch), '--print-data'])
    script.main()
    assert json.loads(capsys.readouterr().out) == fake.batch_scrape.return_value
