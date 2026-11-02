import json
import script

def test_nested_jsonld_entities_are_discovered_once():
    data = {'@type':'Article', 'author':{'@type':['Person','Author']}, 'publisher':{'@type':'Organization', 'employee':[{'@type':'Person'}]}}
    parser = script.HTMLParser('<script type="application/ld+json">' + json.dumps(data) + '</script>')
    assert parser.extract_meta()['json_ld_types'] == ['Article','Person','Author','Organization']
