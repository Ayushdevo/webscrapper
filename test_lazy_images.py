import pytest
import script

@pytest.mark.parametrize('placeholder', ['data:image/gif;base64,AAA', 'javascript:void(0)', 'https://[broken'])
def test_lazy_source_survives_invalid_or_embedded_placeholder(placeholder):
    parser = script.HTMLParser(f'<img src="{placeholder}" data-src="/photo.jpg" alt="lazy"><img src="/photo.jpg" alt="eager">', 'https://example.com')
    assert [img['src'] for img in parser.extract_images()] == ['https://example.com/photo.jpg']
    assert parser.extract_images()[0]['alt'] == 'lazy'
