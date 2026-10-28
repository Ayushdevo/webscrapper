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
