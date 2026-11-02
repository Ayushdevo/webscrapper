from unittest.mock import MagicMock
import pytest
import script

@pytest.mark.parametrize('export', [False, True])
def test_batch_failure_status_preserves_summary(monkeypatch, tmp_path, export):
    batch = tmp_path / 'urls.txt'
    batch.write_text('https://bad.example')
    fake = MagicMock()
    fake.batch_scrape.return_value = [{'url':'https://bad.example', 'error':'offline', 'data':{}}]
    monkeypatch.setattr(script, 'DataPulseScraper', lambda **kw: fake)
    argv = ['script.py', '--batch', str(batch), '--output-dir', str(tmp_path)]
    if export:
        argv += ['--export', 'json']
    monkeypatch.setattr('sys.argv', argv)
    with pytest.raises(SystemExit) as exc:
        script.main()
    assert exc.value.code == 1
    if export:
        assert 'offline' in (tmp_path / 'batch_summary.json').read_text()
