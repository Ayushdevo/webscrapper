import script

def test_hidden_and_template_content_do_not_leak_into_readable_text():
    parser = script.HTMLParser('<main><p>Visible</p><div hidden><p>Hidden</p></div><template><p>Template</p></template><p>End</p></main>')
    assert parser.extract_clean_text()['paragraphs'] == ['Visible','End']
    # Extraction must not mutate the original DOM used by other modes.
    assert parser.soup.find('template') is not None
