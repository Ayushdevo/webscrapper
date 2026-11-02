import script

def test_custom_results_keep_first_occurrence_order():
    parser = script.HTMLParser('<p>$20 $10 $20 $30 $5</p><p>z@example.com a@example.com z@example.com</p><p>+1 234-567-8901</p><p>+1 234-567-8900</p>')
    result = script.extract_custom(parser, 'Extract prices, emails and phone numbers')
    assert result['prices'] == ['$20','$10','$30','$5']
    assert result['emails'] == ['z@example.com','a@example.com']
    assert result['phones'] == ['+1 234-567-8901','+1 234-567-8900']
