import pytest
import script

@pytest.mark.parametrize('html,expected', [
    ('<main>First<br>Second<br>Third</main>', ['First','Second','Third']),
    ('<main><div>First</div><div>Second</div></main>', ['First','Second']),
    ('<main>Before<section>Middle</section>After</main>', ['Before','Middle','After']),
    ('<main><span>First<br>Second</span></main>', ['First','Second']),
])
def test_structural_text_boundaries(html, expected):
    assert script.HTMLParser(html).extract_clean_text()['paragraphs'] == expected
