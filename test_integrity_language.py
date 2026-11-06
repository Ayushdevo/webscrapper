import script
import pytest

@pytest.mark.parametrize('lang', ['zh-Hant-TW', 'sr-Latn-RS', 'en-US', 'hi'])
def test_language_tag_is_preserved(lang):
    parser = script.HTMLParser(f'<html lang="{lang}"><body>Hello</body></html>')
    assert parser.extract_clean_text()['language'] == lang
