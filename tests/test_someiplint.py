import unittest
from someiplint import lint
class SomeIpTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(lint({"service_id":1,"version":{"major":1,"minor":0},"methods":[{"id":1,"name":"M","reliability":"reliable"}],"events":[]}),[])
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
if __name__=="__main__": unittest.main()
