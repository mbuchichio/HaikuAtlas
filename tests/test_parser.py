from __future__ import annotations

import unittest
from pathlib import Path

from haiku_atlas.parser import parse_header_symbols

FIXTURES = Path(__file__).parent / "fixtures" / "real_api"


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

    def test_parse_header_symbols_preserves_qualified_type_names(self) -> None:
        symbols = parse_header_symbols("class BView::Private {};")

        self.assertEqual("Private", symbols[0].name)
        self.assertEqual("BView::Private", symbols[0].qualified_name)

    def test_parse_header_symbols_normalizes_method_declaration_whitespace(self) -> None:
        symbols = parse_header_symbols(
            """
            class BView {
            public:
                virtual\tvoid\t\t\t\tDraw(BRect updateRect);
            };
            """
        )

        self.assertEqual("virtual void Draw(BRect updateRect);", symbols[1].raw_declaration)

    def test_parse_header_symbols_detects_multiline_public_methods(self) -> None:
        symbols = parse_header_symbols(
            """
            class BView {
            public:
                virtual status_t Archive(BMessage* archive,
                    bool deep = true) const;
            };
            """
        )

        self.assertEqual("BView::Archive", symbols[1].qualified_name)
        self.assertEqual(4, symbols[1].line_start)
        self.assertEqual(5, symbols[1].line_end)
        self.assertEqual(
            "virtual status_t Archive(BMessage* archive, bool deep = true) const;",
            symbols[1].raw_declaration,
        )

    def test_parse_header_symbols_handles_api_macros_in_declarations(self) -> None:
        symbols = parse_header_symbols(
            """
            class CPPUNIT_API BTestCase : public CppUnit::TestCase {
            public:
                CPPUNIT_API status_t Run();
                virtual _EXPORT void TearDown();
            };
            """
        )

        self.assertEqual(
            ["BTestCase", "BTestCase::Run", "BTestCase::TearDown"],
            [symbol.qualified_name for symbol in symbols],
        )
        self.assertEqual(("CppUnit::TestCase",), symbols[0].inherits)
        self.assertEqual("class CPPUNIT_API BTestCase : public CppUnit::TestCase {", symbols[0].raw_declaration)
        self.assertEqual("CPPUNIT_API status_t Run();", symbols[1].raw_declaration)

    def test_parse_header_symbols_ignores_truncated_type_declarations(self) -> None:
        symbols = parse_header_symbols("class Broken : public")

        self.assertEqual([], symbols)

    def test_parse_header_symbols_drops_truncated_public_method_before_next_method(self) -> None:
        symbols = parse_header_symbols(
            """
            class BView {
            public:
                virtual status_t Archive(BMessage* archive,
                virtual void Draw(BRect updateRect);
            };
            """
        )

        self.assertEqual(["BView", "BView::Draw"], [symbol.qualified_name for symbol in symbols])

    def test_parse_header_symbols_attaches_section_comments_to_methods(self) -> None:
        symbols = parse_header_symbols(
            """
            class BMessage {
            public:
                // Replying
                status_t SendReply(uint32 command);
                // Flattening data
                status_t Flatten(char* buffer, ssize_t size) const;
            };
            """
        )

        self.assertEqual("Replying", symbols[1].source_context)
        self.assertEqual("Flattening data", symbols[2].source_context)

    def test_parse_header_symbols_keeps_space_before_class_body(self) -> None:
        symbols = parse_header_symbols("class BView : public BHandler\t{")

        self.assertEqual("class BView : public BHandler {", symbols[0].raw_declaration)

    def test_parse_header_symbols_handles_real_haiku_api_excerpts(self) -> None:
        cases = {
            "Application_excerpt.h": [
                "BApplication",
                "BApplication::BApplication",
                "BApplication::~BApplication",
                "BApplication::Instantiate",
                "BApplication::Archive",
                "BApplication::Run",
                "BApplication::Quit",
                "BApplication::QuitRequested",
                "BApplication::MessageReceived",
            ],
            "View_excerpt.h": [
                "BView",
                "BView::BView",
                "BView::BView",
                "BView::~BView",
                "BView::Instantiate",
                "BView::Archive",
                "BView::AttachedToWindow",
                "BView::Draw",
                "BView::MouseDown",
            ],
            "Window_excerpt.h": [
                "BWindow",
                "BWindow::BWindow",
                "BWindow::~BWindow",
                "BWindow::Instantiate",
                "BWindow::Archive",
                "BWindow::Quit",
                "BWindow::Close",
                "BWindow::MessageReceived",
                "BWindow::FrameResized",
            ],
            "Message_excerpt.h": [
                "BMessage",
                "BMessage::BMessage",
                "BMessage::BMessage",
                "BMessage::BMessage",
                "BMessage::~BMessage",
                "BMessage::CountNames",
                "BMessage::IsEmpty",
                "BMessage::PrintToStream",
                "BMessage::FlattenedSize",
            ],
        }

        for fixture_name, expected_names in cases.items():
            with self.subTest(fixture=fixture_name):
                source = (FIXTURES / fixture_name).read_text(encoding="utf-8")
                symbols = parse_header_symbols(source)

                self.assertEqual(expected_names, [symbol.qualified_name for symbol in symbols])


if __name__ == "__main__":
    unittest.main()
