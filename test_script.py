from pathlib import Path
import json
from unittest.mock import MagicMock
import pytest
import script
from script import HTMLParser, Exporter, DataPulseScraper


@pytest.mark.parametrize('payload, expected', [
    ('[{"@type":"Article"},{"@type":["Person","Author"]}]', ['Article','Person','Author']),
    ('{"@graph":[{"@type":"Organization"},{"@type":"Person"}]}', ['Organization','Person']),
    ('null', []), ('42', []), ('"text"', []), ('{broken', []),
])
def test_json_ld_containers(payload, expected):
    parser = HTMLParser('<script type="application/ld+json">' + payload + '</script>')
    assert parser.extract_meta()['json_ld_types'] == expected


def test_document_base_url():
    parser = HTMLParser('<base href="/assets/"><a href="guide">Guide</a>'
                        '<img src="cover.png"><link rel="canonical" href="page">',
                        'https://example.com/articles/start')
    assert parser.extract_links()[0]['href'] == 'https://example.com/assets/guide'
    assert parser.extract_images()[0]['src'] == 'https://example.com/assets/cover.png'
    assert parser.extract_meta()['canonical'] == 'https://example.com/assets/page'
    external = HTMLParser('<base href="https://cdn.example.org/"><a href="x">X</a>',
                          'https://example.com/')
    assert external.extract_links()[0]['type'] == 'external'


def test_only_http_links_with_hosts():
    parser = HTMLParser('<a href="httpx://example.com/x">Bad</a>'
                        '<a href="https:///missing">Bad</a>'
                        '<a href="https://valid.example/x">Good</a>')
    assert [x['href'] for x in parser.extract_links()] == ['https://valid.example/x']


@pytest.mark.parametrize('html, expected', [
    ('<main><h1>Hi</h1><p>Short text.</p></main>', ['Hi', 'Short text.']),
    ('<body>Plain body text</body>', ['Plain body text']),
    ('<main><h6>Small heading</h6></main>', ['Small heading']),
    ('<body><script>ignore()</script></body>', []),
])
def test_short_and_plain_text(html, expected):
    result = HTMLParser(html).extract_clean_text()
    assert result['paragraphs'] == expected
    assert result['word_count'] == len(' '.join(expected).split())


@pytest.mark.parametrize('html, expected', [
    ('<blockquote><p>A quoted sentence.</p></blockquote>', ['A quoted sentence.']),
    ('<ul><li>Parent<ul><li>Child</li></ul>Tail</li></ul>', ['Parent', 'Child', 'Tail']),
    ('<main><p>One <em>two</em> three.</p><p>One <em>two</em> three.</p></main>',
     ['One two three.', 'One two three.']),
])
def test_nested_text_once(html, expected):
    assert HTMLParser(html).extract_clean_text()['paragraphs'] == expected


def test_table_counts_and_row_headers():
    table = HTMLParser('<table><tr><th>Name</th><th>Value</th></tr>'
                       '<tr><th>A</th><td>1</td></tr><tr><th>B</th><td>2</td></tr></table>').extract_tables()[0]
    assert table['headers'] == ['Name', 'Value']
    assert table['rows'] == [['A', '1'], ['B', '2']]
    assert table['row_count'] == 2
    assert table['col_count'] == 2

def test_nested_table_rows_not_counted_in_parent():
    tables = HTMLParser('<table><tr><td>Outer<table><tr><td>Inner</td></tr></table>'
                        '</td></tr></table>').extract_tables()
    assert [t['row_count'] for t in tables] == [1, 1]

def test_table_body_th_does_not_become_column_heading():
    table = HTMLParser('<table><tr><td>A</td><td>1</td></tr>'
                       '<tr><th>B</th><td>2</td></tr></table>').extract_tables()[0]
    assert table['headers'] == ['col_1', 'col_2']
    assert table['row_count'] == 2


def test_image_url_normalization():
    parser = HTMLParser('<img src=" /cover.png "><img src="https://example.com/cover.png">'
                        '<img src="data:image/png;base64,AAA"><img src="javascript:bad()">'
                        '<img src="   " data-src="/lazy.png">', 'https://example.com/')
    assert [x['src'] for x in parser.extract_images()] == [
        'https://example.com/cover.png', 'https://example.com/lazy.png']
