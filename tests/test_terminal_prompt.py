import io
import unittest
from unittest import mock

from skillz.context import confirm_on_terminal


def ask(answer: str | type[BaseException], is_terminal: bool = True) -> tuple[bool, str]:
    stderr = io.StringIO()
    replies = mock.Mock(side_effect=answer) if isinstance(answer, type) else mock.Mock(return_value=answer)
    with (
        mock.patch("sys.stdin.isatty", return_value=is_terminal),
        mock.patch("builtins.input", replies),
        mock.patch("sys.stderr", stderr),
    ):
        return confirm_on_terminal("Proceed?"), stderr.getvalue()


class ConfirmOnTerminalTest(unittest.TestCase):
    def test_yes_answers_confirm(self) -> None:
        for answer in ("y", "Y", "yes", " yes "):
            with self.subTest(answer=answer):
                self.assertTrue(ask(answer)[0])

    def test_anything_else_declines(self) -> None:
        for answer in ("", "n", "nope"):
            with self.subTest(answer=answer):
                self.assertFalse(ask(answer)[0])

    def test_end_of_input_declines_without_crashing(self) -> None:
        self.assertEqual(ask(EOFError), (False, "\n"))

    def test_no_terminal_declines_and_says_why(self) -> None:
        confirmed, stderr = ask("y", is_terminal=False)
        self.assertFalse(confirmed)
        self.assertIn("no terminal to ask on", stderr)


if __name__ == "__main__":
    unittest.main()
