import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BODY = (ROOT / "evidence/ti-accuracy.json").read_bytes()
COMMIT = "964b7e115b8ba21b928ac3905e8259752bec40e7"
BUYER = "buyer"
OTHER = "other"


class UserError(Exception):
    pass


class Contract:
    def __new__(cls):
        obj = super().__new__(cls)
        for field in ("approved", "checklists", "decisions"):
            setattr(obj, field, {})
        return obj


identity = lambda func: func
message = types.SimpleNamespace(sender_address=BUYER)
response = types.SimpleNamespace(status_code=200, body=BODY)
gl = types.SimpleNamespace(
    Contract=Contract, UserError=UserError, message=message,
    public=types.SimpleNamespace(view=identity, write=identity),
    eq_principle=types.SimpleNamespace(strict_eq=lambda fn: fn()),
    nondet=types.SimpleNamespace(web=types.SimpleNamespace(get=lambda _: response)),
)
sys.modules["genlayer"] = types.SimpleNamespace(gl=gl, Address=str, TreeMap=dict)
spec = importlib.util.spec_from_file_location("spec_match", ROOT / "contracts/spec_match.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SpecMatchTests(unittest.TestCase):
    def setUp(self):
        message.sender_address = BUYER
        response.status_code, response.body = 200, BODY
        self.contract = module.SpecMatch()
        self.requirements = '[["Cold-start accuracy",-15,45,20,"cC"],["Indoor accuracy",0,45,200,"mC"]]'
        self.contract.lock_checklist("cold-start", self.requirements)

    def review(self, part):
        self.contract.review("cold-start", part, COMMIT)
        return json.loads(self.contract.get_review("cold-start", part, COMMIT))

    def test_authoritative_examples(self):
        self.assertEqual([r["status"] for r in self.review("TMP117")["requirements"]], ["MET", "MET"])
        rows = self.review("TMP116")["requirements"]
        self.assertEqual([r["status"] for r in rows], ["FAILED", "MET"])
        self.assertEqual([r["guarantee_mC"] for r in rows], [250, 200])
        self.assertIn("footnote 1", rows[0]["citations"][0])

    def test_deterministic_decision_hash(self):
        result = self.review("TMP117")
        self.assertEqual(result.pop("decision_sha256"), module.digest(module.encode(result).encode()))
        self.assertEqual(result["evidence_sha256"], module.digest(BODY))

    def test_public_review_and_replay_rejection(self):
        message.sender_address = OTHER
        self.review("TMP117")
        with self.assertRaisesRegex(UserError, "already recorded"):
            self.review("TMP117")

    def test_only_buyer_can_lock_and_approve(self):
        message.sender_address = OTHER
        with self.assertRaises(UserError):
            self.contract.lock_checklist("other", self.requirements)
        with self.assertRaises(UserError):
            self.contract.approve_snapshot("a" * 40, "a" * 64)

    def test_locked_ids_cannot_be_replaced(self):
        with self.assertRaisesRegex(UserError, "already locked"):
            self.contract.lock_checklist("cold-start", self.requirements)

    def test_hash_mismatch_and_retry(self):
        response.body = BODY + b" "
        with self.assertRaisesRegex(UserError, "hash mismatch"):
            self.review("TMP116")
        self.assertEqual(self.contract.get_review("cold-start", "TMP116", COMMIT), "")
        response.body = BODY
        self.review("TMP116")

    def test_http_error(self):
        response.body = b""
        with self.assertRaisesRegex(UserError, "unavailable"):
            self.review("TMP117")

    def test_unknown_part(self):
        with self.assertRaisesRegex(UserError, "no valid evidence"):
            self.review("UNKNOWN")

    def test_unapproved_commit(self):
        with self.assertRaisesRegex(UserError, "not registered"):
            self.contract.review("cold-start", "TMP117", "f" * 40)

    def test_reject_invalid_checklists(self):
        for invalid in ('{}', '[[1,0,1,1,"mC"]]', '[["a",0,0,1,"mC"]]',
                        '[["a",0,1,true,"mC"]]', '[["a",0,1,1,"V"]]',
                        '[["a",0,1,1,"mC"],[" a ",0,1,1,"mC"]]'):
            with self.subTest(invalid=invalid), self.assertRaises(UserError):
                module.parse_checklist(invalid)

    def test_segments_and_gap(self):
        rows = [[-10, 0, 150, "left"], [0, 10, 200, "right"]]
        checklist = [["covered", -10, 10, 200], ["gap", -15, 10, 200]]
        met, gap = module.assess(checklist, rows)
        self.assertEqual((met["status"], met["citations"]), ("MET", ["left", "right"]))
        self.assertEqual((gap["status"], gap["uncovered_C"]), ("UNVERIFIED", [[-15, -10]]))


if __name__ == "__main__":
    unittest.main()
