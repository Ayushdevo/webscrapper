import script

def test_metadata_names_and_relation_tokens_are_case_insensitive():
    meta = script.HTMLParser('<meta name="DESCRIPTION" content="Hello"><meta property="OG:TITLE" content="Social"><meta name="Twitter:CARD" content="summary"><link rel="CANONICAL" href="/page">', 'https://example.com').extract_meta()
    assert meta['description'] == 'Hello'
    assert meta['og_title'] == 'Social'
    assert meta['twitter_card'] == 'summary'
    assert meta['canonical'] == 'https://example.com/page'
