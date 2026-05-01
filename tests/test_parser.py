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

    def test_parse_header_symbols_detects_public_methods_only(self) -> None:
        symbols = parse_header_symbols(
            """
            class BView : public BHandler {
            public:
                BView(BRect frame);
                virtual ~BView();
                virtual void Draw(BRect update);
                void MouseDown(BPoint where);

            protected:
                void ProtectedHook();

            private:
                void PrivateHook();
            };
            """
        )

        self.assertEqual(
            ["BView", "BView::BView", "BView::~BView", "BView::Draw", "BView::MouseDown"],
            [symbol.qualified_name for symbol in symbols],
        )
        self.assertEqual(
            ["class", "constructor", "destructor", "method", "method"],
            [symbol.kind for symbol in symbols],
        )
        self.assertEqual("BView", symbols[3].parent_qualified_name)

    def test_parse_header_symbols_treats_struct_methods_as_public_by_default(self) -> None:
        symbols = parse_header_symbols(
            """
            struct BPoint {
                BPoint(float x, float y);
                void PrintToStream() const;
            };
            """
        )

        self.assertEqual(
            ["BPoint", "BPoint::BPoint", "BPoint::PrintToStream"],
            [symbol.qualified_name for symbol in symbols],
        )

    def test_parse_header_symbols_handles_one_line_type_before_enum(self) -> None:
        symbols = parse_header_symbols(
            """
            struct rgb_color {};
            enum orientation {};
            """
        )

        self.assertEqual(
            ["rgb_color", "orientation"],
            [symbol.qualified_name for symbol in symbols],
        )


if __name__ == "__main__":
    unittest.main()
