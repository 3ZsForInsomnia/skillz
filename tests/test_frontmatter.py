import unittest

from skillz.frontmatter import read_frontmatter


def frontmatter(body: str) -> str:
    return f"---\n{body}\n---\n\n# Heading\n"


class ReadFrontmatterTest(unittest.TestCase):
    def test_reads_plain_fields(self) -> None:
        result = read_frontmatter(frontmatter("name: pdf\ndescription: Work with PDFs."))
        self.assertEqual(result, {"name": "pdf", "description": "Work with PDFs."})

    def test_unquotes_double_quoted_values(self) -> None:
        result = read_frontmatter(frontmatter('description: "Say \\"hi\\": now"'))
        self.assertEqual(result["description"], 'Say "hi": now')

    def test_unquotes_single_quoted_values(self) -> None:
        result = read_frontmatter(frontmatter("description: 'It''s fine'"))
        self.assertEqual(result["description"], "It's fine")

    def test_folds_block_scalar(self) -> None:
        result = read_frontmatter(frontmatter("description: >\n  First line\n  second line.\nname: x"))
        self.assertEqual(result["description"], "First line second line.")
        self.assertEqual(result["name"], "x")

    def test_keeps_newlines_in_literal_block(self) -> None:
        result = read_frontmatter(frontmatter("description: |\n  One\n  Two"))
        self.assertEqual(result["description"], "One\nTwo")

    def test_joins_multiline_plain_value(self) -> None:
        result = read_frontmatter(frontmatter("description: Starts here\n  and continues."))
        self.assertEqual(result["description"], "Starts here and continues.")

    def test_nested_mapping_reads_as_empty_and_does_not_leak(self) -> None:
        result = read_frontmatter(frontmatter("metadata:\n  author: someone\ndescription: Real."))
        self.assertEqual(result["metadata"], "")
        self.assertEqual(result["description"], "Real.")
        self.assertNotIn("author", result)

    def test_unknown_fields_are_kept_not_rejected(self) -> None:
        result = read_frontmatter(frontmatter("alwaysApply: false\nversion: 1.2"))
        self.assertEqual(result, {"alwaysApply": "false", "version": "1.2"})

    def test_text_without_frontmatter_is_empty(self) -> None:
        self.assertEqual(read_frontmatter("# Just markdown\n"), {})

    def test_unclosed_frontmatter_is_empty(self) -> None:
        self.assertEqual(read_frontmatter("---\nname: pdf\n"), {})

    def test_ignores_comment_lines(self) -> None:
        result = read_frontmatter(frontmatter("# a comment\nname: pdf"))
        self.assertEqual(result, {"name": "pdf"})


if __name__ == "__main__":
    unittest.main()
