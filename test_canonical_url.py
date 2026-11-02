import pytest
import script

@pytest.mark.parametrize('href,expected', [(' /page ', 'https://example.com/page'), ('javascript:alert(1)',''), ('https://[broken',''), ('mailto:a@example.com','')])
def test_canonical_references_are_valid_web_urls(href, expected):
    parser = script.HTMLParser(f'<link rel="canonical" href="{href}">', 'https://example.com')
    assert parser.extract_meta()['canonical'] == expected
