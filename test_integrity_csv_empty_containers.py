import csv
import script
import pytest

@pytest.mark.parametrize('value,expected', [([], '[]'), ({}, '{}')])
def test_csv_preserves_empty_container_values(tmp_path, value, expected):
    path = script.Exporter(str(tmp_path)).to_csv({'data': value}, 'https://example.com', 'auto')
    with open(path, newline='') as stream:
        assert list(csv.DictReader(stream)) == [{'key': 'data', 'value': expected}]
