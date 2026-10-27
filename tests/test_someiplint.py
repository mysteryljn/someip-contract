import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from someiplint import lint, main
class SomeIpTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(lint({"service_id":1,"version":{"major":1,"minor":0},"methods":[{"id":1,"name":"M","reliability":"reliable"}],"events":[]}),[])

    def test_method_names_must_contain_non_whitespace(self):
        errors = lint({
            "service_id": 1,
            "version": {"major": 1, "minor": 0},
            "methods": [{"id": 1, "name": "   ", "reliability": "reliable"}],
            "events": [],
        })
        self.assertIn("methods[0]: name is required", errors)

    def test_collision(self):
        errors=lint({"service_id":1,"version":{"major":1,"minor":0},"methods":[{"id":2,"name":"M","reliability":"reliable"}],"events":[{"id":2,"reliability":"reliable"}]})
        self.assertTrue(any("collision" in e for e in errors))

    def test_non_object_contract_is_reported(self):
        # Valid JSON such as an array must be rejected as a contract instead
        # of making the library API raise AttributeError on ``spec.get``.
        errors = lint([{"service_id": 1}])
        self.assertEqual(errors, ["contract must be a JSON object"])

    def test_boolean_numeric_fields_are_rejected(self):
        # bool subclasses int in Python, but JSON true/false are not valid
        # SOME/IP identifiers or version components.
        errors = lint({
            "service_id": True,
            "version": {"major": True, "minor": False},
            "methods": [{"id": True, "name": "M", "reliability": "reliable"}],
            "events": [{"id": False, "reliability": "reliable"}],
        })
        self.assertIn("service_id must be uint16", errors)
        self.assertIn("version must contain non-negative major/minor", errors)
        self.assertIn("methods[0]: method id must be uint16", errors)
        self.assertIn("events[0]: event id must be uint16", errors)

    def test_service_discovery_service_id_is_reserved(self):
        # 0xFFFF identifies SOME/IP Service Discovery and cannot identify an
        # application service without colliding with SD traffic.
        errors = lint({
            "service_id": 0xFFFF,
            "version": {"major": 1, "minor": 0},
            "methods": [{"id": 1, "name": "M", "reliability": "reliable"}],
            "events": [],
        })
        self.assertIn(
            "service_id 0xffff is reserved for SOME/IP Service Discovery",
            errors,
        )

    def test_reserved_service_id_zero_is_rejected(self):
        errors = lint({
            "service_id": 0,
            "version": {"major": 1, "minor": 0},
            "methods": [],
            "events": [],
        })
        self.assertIn("service_id 0x0000 is reserved", errors)

    def test_reserved_method_and_event_ids_are_rejected(self):
        # SOME/IP-SD reserves these values for protocol traffic and magic
        # cookie messages.  An application contract must not claim them.
        reserved = (0x0000, 0x7fff, 0x8000, 0xffff)
        errors = lint({
            "service_id": 1,
            "version": {"major": 1, "minor": 0},
            "methods": [
                {"id": ident, "name": "M%d" % ident, "reliability": "reliable"}
                for ident in reserved
            ],
            "events": [
                {"id": ident, "reliability": "unreliable"}
                for ident in reserved
            ],
        })
        for ident in reserved:
            self.assertIn(
                "methods[%d]: method id 0x%04x is reserved" % (reserved.index(ident), ident),
                errors,
            )
            self.assertIn(
                "events[%d]: event id 0x%04x is reserved" % (reserved.index(ident), ident),
                errors,
            )

    def test_version_components_must_fit_wire_uint8(self):
        # The SOME/IP interface version is encoded in an 8-bit header field.
        # Values above 255 would be truncated by a serializer and could make
        # incompatible interfaces appear to use the same version.
        errors = lint({
            "service_id": 1,
            "version": {"major": 256, "minor": 300},
            "methods": [],
            "events": [],
        })
        self.assertIn("version major/minor must fit uint8 (0..255)", errors)

    def test_unhashable_ids_are_reported_without_crashing(self):
        # JSON arrays and objects are invalid IDs.  They used to raise
        # TypeError while the linter built duplicate/collision sets, which
        # made malformed contracts crash CI instead of returning diagnostics.
        errors = lint({
            "service_id": 1,
            "version": {"major": 1, "minor": 0},
            "methods": [{"id": [], "name": "M", "reliability": "reliable"}],
            "events": [{"id": {"raw": 2}, "reliability": "reliable"}],
        })
        self.assertIn("methods[0]: method id must be uint16", errors)
        self.assertIn("events[0]: event id must be uint16", errors)

    def test_mixed_hashable_invalid_ids_do_not_break_collision_check(self):
        # Sorting an int and a string directly raises TypeError on Python 3.
        errors = lint({
            "service_id": 1,
            "version": {"major": 1, "minor": 0},
            "methods": [
                {"id": 2, "name": "M", "reliability": "reliable"},
                {"id": "raw", "name": "N", "reliability": "reliable"},
            ],
            "events": [
                {"id": 2, "reliability": "reliable"},
                {"id": "raw", "reliability": "reliable"},
            ],
        })
        self.assertIn("method/event id collision 2", errors)
        self.assertIn("method/event id collision raw", errors)

    def test_cli_reports_deeply_nested_json_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contract.json"
            path.write_text("[" * 3000 + "]" * 3000, encoding="utf-8")
            # JSON decoder depth limits differ across supported Python
            # versions: some raise RecursionError while newer decoders parse
            # the array and let the contract-shape validator return 1.
            self.assertIn(main([str(path)]), (1, 2))
            # Exercise the error-handling branch directly so the regression
            # remains meaningful even when the runtime accepts this depth.
            with patch("someiplint.json.loads", side_effect=RecursionError("deep JSON")):
                self.assertEqual(main([str(path)]), 2)

if __name__=="__main__": unittest.main()
