from unittest.mock import MagicMock
import script

def test_batch_forwards_custom_prompt(tmp_path):
    scraper = script.DataPulseScraper(output_dir=tmp_path)
    scraper.scrape = MagicMock(return_value={'data': {'emails': []}})
    scraper.batch_scrape(['https://example.com'], mode='custom', custom_prompt='Extract emails')
    scraper.scrape.assert_called_once_with('https://example.com', mode='custom', export=None, custom_prompt='Extract emails')

def test_cli_batch_forwards_prompt(monkeypatch, tmp_path):
    batch = tmp_path / 'urls.txt'
    batch.write_text('https://example.com')
    fake = MagicMock()
    fake.batch_scrape.return_value = []
    monkeypatch.setattr(script, 'DataPulseScraper', lambda **kw: fake)
    monkeypatch.setattr('sys.argv', ['script.py', '--batch', str(batch), '--mode', 'custom', '--prompt', 'Extract emails'])
    script.main()
    assert fake.batch_scrape.call_args.kwargs['custom_prompt'] == 'Extract emails'
