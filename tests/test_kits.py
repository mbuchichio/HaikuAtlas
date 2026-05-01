from __future__ import annotations

import unittest

from haiku_atlas.kits import infer_kit_name, kit_display_name


class KitTests(unittest.TestCase):
    def test_infer_kit_name_from_public_header_path(self) -> None:
        self.assertEqual("interface", infer_kit_name("os/interface/View.h"))

    def test_infer_kit_name_from_public_aggregate_header_path(self) -> None:
        self.assertEqual("interface", infer_kit_name("os/InterfaceKit.h"))

    def test_infer_kit_name_from_private_header_path(self) -> None:
        self.assertEqual("app", infer_kit_name("private/app/ApplicationPrivate.h"))

    def test_infer_kit_name_ignores_unknown_private_subsystems(self) -> None:
        self.assertIsNone(infer_kit_name("private/debugger/value/Value.h"))

    def test_infer_kit_name_returns_none_for_unknown_path(self) -> None:
        self.assertIsNone(infer_kit_name("glibc/printf.h"))

    def test_kit_display_name_uses_known_names(self) -> None:
        self.assertEqual("Interface Kit", kit_display_name("interface"))


if __name__ == "__main__":
    unittest.main()
