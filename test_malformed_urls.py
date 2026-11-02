import pytest
import script

@pytest.mark.parametrize('bad', ['https://[broken', 'http://example.com:bad/x', 'http://example.com:99999/x', 'http://exa mple.com/x'])
def test_bad_link_and_image_do_not_abort_valid_results(bad):
    parser = script.HTMLParser(f'<a href="{bad}">Bad</a><a href="/good">Good</a><img src="{bad}"><img src="/good.png">', 'https://example.com')
    assert [x['href'] for x in parser.extract_links()] == ['https://example.com/good']
    assert [x['src'] for x in parser.extract_images()] == ['https://example.com/good.png']

def test_malformed_base_falls_back_to_document_url():
    parser = script.HTMLParser('<base href="https://[broken"><a href="/good">Good</a>', 'https://example.com')
    assert parser.extract_links()[0]['href'] == 'https://example.com/good'
