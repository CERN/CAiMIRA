import re

import jinja2
import mistune

HEADER_PATTERN = re.compile(r'\n(#+)(.*)')


def _block_headings(contents: str):
    """
    Return the headings (and the start/end positions of their blocks) of
    markdown, in reverse order.

    Note that a block ends when the next heading is found, even if that heading
    is a sub-block of the current one.

    """
    all_block_headings = HEADER_PATTERN.finditer(
        '\n' + contents, re.MULTILINE & re.DOTALL
    )

    end_pos = None
    for result in list(all_block_headings)[::-1]:
        heading = {
            'start_pos': result.end(),
            'end_pos': end_pos,
            'depth': len(result[1]),
            'heading': result[2].strip(),
        }
        end_pos = result.start()
        yield heading


def extract_block(block_name: str, contents: str) -> str:
    """
    Extract the given header block from the given markdown.

    The result *does not* contain the children headers of the block.

    """
    for block in _block_headings(contents):
        if block['heading'] == block_name:
            return contents[block['start_pos']: block['end_pos']]
    else:
        raise ValueError(f"Heading \"{ block_name }\" not found")


def extract_headings(contents: str) -> list:
    """
    Extract all headers from the given markdown.

    """
    headings = []
    for block in _block_headings(contents):
        headings.append(block['heading'])
    return headings


def extract_rendered_markdown_blocks(template: jinja2.Template) -> dict:
    """
    Return a dictionary of all common markdown text blocks, rendered to HTML and
    uniquely identified by their headings, from the given Jinja2 template.

    """
    common_text = template.render()
    headings = extract_headings(common_text)
    text_blocks = {}
    for heading in headings:
        block = extract_block(heading, common_text)
        html_content = mistune.markdown(block, escape=False)
        text_blocks[heading] = html_content
    return text_blocks
