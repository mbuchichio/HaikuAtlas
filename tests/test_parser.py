from __future__ import annotations

import unittest

from haiku_atlas.parser import parse_header_symbols


class ParserTests(unittest.TestCase):
    def test_parse_header_symbols_detects_class_struct_enum_and_inheritance(self) -> None:
        symbols = parse_header_symbols(
            """
            class BView : public BHandler {
            };

            struct rgb_color {
            };

            enum orientation {
                B_HORIZONTAL,
                B_VERTICAL
            };
            """
        )

        self.assertEqual(["class", "struct", "enum"], [symbol.kind for symbol in symbols])
        self.assertEqual(["BView", "rgb_color", "orientation"], [symbol.name for symbol in symbols])
        self.assertEqual(("BHandler",), symbols[0].inherits)

    def test_parse_header_symbols_ignores_forward_declarations(self) -> None:
        symbols = parse_header_symbols(
            """
            class BView;
            struct rgb_color;
            enum orientation;
            """
        )

        self.assertEqual([], symbols)


if __name__ == "__main__":
    unittest.main()

