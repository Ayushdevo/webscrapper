import pytest
import script

@pytest.mark.parametrize('url', ['https://EXAMPLE.com/page', 'https://example.com:443/page', 'http://example.com/page'])
def test_same_host_links_remain_internal(url):
    assert script.HTMLParser(f'<a href="{url}">Page</a>', 'https://example.com').extract_links()[0]['type'] == 'internal'

def test_other_hostname_is_external():
    assert script.HTMLParser('<a href="https://example.com.evil.test">Page</a>', 'https://example.com').extract_links()[0]['type'] == 'external'
