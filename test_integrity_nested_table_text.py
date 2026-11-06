import script

def test_parent_cell_does_not_repeat_nested_table_text():
    tables = script.HTMLParser('<table><tr><td>Before<table><tr><td>Inner</td></tr></table>After</td></tr></table>').extract_tables()
    assert tables[0]['rows'] == [['Before After']]
    assert tables[1]['rows'] == [['Inner']]
