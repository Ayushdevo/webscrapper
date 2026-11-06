import script
import pytest

@pytest.mark.parametrize('mime', ['APPLICATION/LD+JSON', 'application/ld+json; charset=utf-8', ' Application/LD+JSON '])
def test_json_ld_media_type_is_case_insensitive(mime):
    parser = script.HTMLParser('<script type="' + mime + '">{"@type":"Article"}</script>')
    assert parser.extract_meta()['json_ld_types'] == ['Article']

def test_non_json_ld_script_stays_excluded():
    assert script.HTMLParser('<script type="text/javascript">{"@type":"Article"}</script>').extract_meta()['json_ld_types'] == []
