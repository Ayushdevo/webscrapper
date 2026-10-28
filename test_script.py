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
