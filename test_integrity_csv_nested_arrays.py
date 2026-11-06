import csv
import script

def test_csv_recurses_through_nested_arrays(tmp_path):
    path = script.Exporter(str(tmp_path)).to_csv({'matrix': [[1, 2], [{'x': 3}]]}, 'https://example.com', 'auto')
    with open(path, newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert rows == [{'key': 'matrix.[0].[0]', 'value': '1'},
                    {'key': 'matrix.[0].[1]', 'value': '2'},
                    {'key': 'matrix.[1].[0].x', 'value': '3'}]
