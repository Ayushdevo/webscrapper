import script

def test_colspan_keeps_following_cells_aligned():
    table = script.HTMLParser('<table><tr><th colspan="2">Group</th><th>Count</th></tr><tr><td>A</td><td>B</td><td>3</td></tr></table>').extract_tables()[0]
    assert table['headers'] == ['Group', 'Group', 'Count']
    assert table['rows'] == [['A', 'B', '3']]
    assert table['col_count'] == 3

def test_rowspan_keeps_following_rows_aligned():
    table = script.HTMLParser('<table><tr><th>Name</th><th>Value</th></tr><tr><td rowspan="2">A</td><td>1</td></tr><tr><td>2</td></tr></table>').extract_tables()[0]
    assert table['rows'] == [['A', '1'], ['A', '2']]

def test_zero_rowspan_stops_at_row_group_boundary():
    table = script.HTMLParser('<table><tbody><tr><td rowspan="0">A</td><td>1</td></tr><tr><td>2</td></tr></tbody><tbody><tr><td>B</td><td>3</td></tr></tbody></table>').extract_tables()[0]
    assert table['rows'] == [['A', '1'], ['A', '2'], ['B', '3']]

def test_invalid_span_defaults_and_large_span_is_bounded():
    table = script.HTMLParser('<table><tr><td colspan="bad">A</td><td rowspan="-2">B</td></tr></table>').extract_tables()[0]
    assert table['rows'] == [['A', 'B']]
    table = script.HTMLParser('<table><tr><td colspan="1000000000">A</td></tr></table>').extract_tables()[0]
    assert table['col_count'] == 1000


def test_negative_rowspan_does_not_extend_to_following_rows():
    table = script.HTMLParser('<table><tr><td rowspan="-2">A</td><td>1</td></tr><tr><td>B</td><td>2</td></tr></table>').extract_tables()[0]
    assert table['rows'] == [['A', '1'], ['B', '2']]
