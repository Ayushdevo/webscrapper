import json
import script
import pytest

@pytest.mark.parametrize('value', [float('nan'), float('inf'), object(), '\ud800'])
def test_invalid_json_export_leaves_no_partial_artifact(tmp_path, value):
    exporter = script.Exporter(str(tmp_path))
    with pytest.raises((ValueError, TypeError, UnicodeError)):
        exporter.to_json({'bad': value}, 'https://example.com', 'auto')
    assert not list(tmp_path.iterdir())

def test_json_export_retains_unicode(tmp_path):
    path = script.Exporter(str(tmp_path)).to_json({'name': 'नमस्ते'}, 'https://example.com', 'auto')
    with open(path, encoding='utf-8') as stream:
        assert json.load(stream)['data'] == {'name': 'नमस्ते'}
