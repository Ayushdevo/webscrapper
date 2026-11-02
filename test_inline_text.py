import script

def test_inline_text_does_not_concatenate_words():
    parser = script.HTMLParser('<title>Hello world</title><h1>Hello <em>world</em></h1><a href="https://example.com">Read <strong>more</strong></a>')
    assert parser.extract_meta()['title'] == 'Hello world'
    assert parser.extract_headings() == [{'level':'h1', 'text':'Hello world'}]
    assert parser.extract_links()[0]['text'] == 'Read more'
