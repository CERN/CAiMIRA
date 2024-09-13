import textwrap

import jinja2
import pytest

import cern_caimira.apps.calculator.markdown_tools as md_tools


@pytest.fixture
def example_template():
    return jinja2.Environment().from_string(textwrap.dedent("""
        # A header

        Some *text*

        {% block using_jinja_blocks %}
        # Another header

        Some more **text**.
        {% endblock %}

    """))


def test_extract_blocks(example_template):
    blocks = md_tools.extract_rendered_markdown_blocks(example_template)
    assert 'A header' in blocks
    assert blocks['A header'] == '<p>Some <em>text</em></p>\n'
    assert 'Another header' in blocks
    assert blocks['Another header'] == '<p>Some more <strong>text</strong>.</p>\n'
