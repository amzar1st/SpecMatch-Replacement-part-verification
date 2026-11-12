# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import hashlib
import json
import re

EVIDENCE_ROOT = "https://raw.githubusercontent.com/amzar1st/SpecMatch-Replacement-part-verification/"
PROFILE = "3v3-8avg-1hz"


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(body):
    return hashlib.sha256(body).hexdigest()


def bounded(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise gl.UserError("Integer outside permitted range")
    return value


def millidegrees(value, unit):
    amount = bounded(value, 1, 100_000)
    if unit == "mC":
        return amount
    if unit == "cC":
        return amount * 10
    raise gl.UserError("Accuracy unit must be mC or cC")


def interval(low, high):
    bounded(low, -273, 1000)
    bounded(high, -273, 1000)
    if low >= high:
        raise gl.UserError("Temperature interval must have positive width")


def parse_checklist(text):
    if len(text) > 1500:
        raise gl.UserError("Checklist exceeds size limit")
    try:
        data = json.loads(text)
    except ValueError:
        raise gl.UserError("Checklist must be valid JSON")
    if not isinstance(data, list) or not 1 <= len(data) <= 8:
        raise gl.UserError("Use one to eight checklist rows")
    result = []
    seen = set()
    for row in data:
        if not isinstance(row, list) or len(row) != 5:
            raise gl.UserError("Use [label, lowC, highC, limit, unit]")
        label, low, high, amount, unit = row
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 64 or label.strip() in seen:
            raise gl.UserError("Checklist labels must be distinct")
        label = label.strip()
        seen.add(label)
        interval(low, high)
        result.append([label, low, high, millidegrees(amount, unit)])
    return result


def extract(body, part):
    data = json.loads(body)
    if data["schema"] != "specmatch/1" or data["profile"] != PROFILE:
        raise ValueError("Unsupported evidence profile")
    entry = data["parts"][part]
    if not isinstance(entry["revision"], str) or not 1 <= len(entry["revision"]) <= 40:
        raise ValueError("Invalid revision")
    if not re.fullmatch(r"https://www\.ti\.com/lit/ds/[A-Za-z0-9/_.-]+\.pdf(?:#page=[0-9]{1,3})?", entry["source"]):
        raise ValueError("Unsupported manufacturer citation")
    if not 1 <= len(entry["rows"]) <= 16:
        raise ValueError("Invalid evidence row count")
    rows = []
    for low, high, amount, unit, cite in entry["rows"]:
        interval(low, high)
        if not isinstance(cite, str) or not 1 <= len(cite) <= 140:
            raise ValueError("Invalid table citation")
        rows.append([low, high, millidegrees(amount, unit), cite])
    return {"revision": entry["revision"], "source": entry["source"], "rows": sorted(rows)}


def assess(checklist, rows):
    results = []
    for label, low, high, limit in checklist:
        edges = {low, high}
        for start, end, _, _ in rows:
            if low < start < high:
                edges.add(start)
            if low < end < high:
                edges.add(end)
        edges = sorted(edges)
        gaps = []
        citations = set()
        worst = None
        for left, right in zip(edges, edges[1:]):
            candidates = [(amount, cite) for start, end, amount, cite in rows if start <= left and end >= right]
            if not candidates:
                gaps.append([left, right])
                continue
            amount, citation = min(candidates)
            worst = amount if worst is None else max(worst, amount)
            citations.add(citation)
        status = "UNVERIFIED" if gaps else ("MET" if worst <= limit else "FAILED")
        results.append({"label": label, "status": status, "max_mC": limit, "guarantee_mC": None if gaps else worst,
                        "range_C": [low, high], "citations": sorted(citations), "uncovered_C": gaps})
    return results


class SpecMatch(gl.Contract):
    curator: Address
    approved: TreeMap[str, str]
    checklists: TreeMap[str, str]
    decisions: TreeMap[str, str]

    def __init__(self):
        self.curator = gl.message.sender_address
        self.approved["964b7e115b8ba21b928ac3905e8259752bec40e7"] = "8dce431969cb5b12b1f210d687bba9d0895bdb5c68e4f053e96525d5349a1cb4"

    @gl.public.write
    def approve_snapshot(self, commit: str, sha256: str) -> None:
        if gl.message.sender_address != self.curator:
            raise gl.UserError("Only the curator can approve a snapshot")
        if not re.fullmatch("[0-9a-f]{40}", commit) or not re.fullmatch("[0-9a-f]{64}", sha256):
            raise gl.UserError("Use full lowercase commit and SHA-256")
        if commit in self.approved:
            raise gl.UserError("Snapshot is already approved")
        self.approved[commit] = sha256

    @gl.public.write
    def lock_checklist(self, checklist_id: str, requirements_json: str) -> None:
        if not re.fullmatch("[a-z0-9-]{3,32}", checklist_id):
            raise gl.UserError("Invalid checklist slug")
        if gl.message.sender_address != self.curator:
            raise gl.UserError("Only the buyer can lock a checklist")
        if checklist_id in self.checklists:
            raise gl.UserError("Checklist ID is already locked")
        rows = parse_checklist(requirements_json)
        self.checklists[checklist_id] = encode({"profile": PROFILE, "requirements": rows})

    @gl.public.write
    def review(self, checklist_id: str, part: str, commit: str) -> None:
        if not re.fullmatch("[a-z0-9-]{3,32}", checklist_id) or not re.fullmatch("[A-Z0-9-]{2,24}", part) or not re.fullmatch("[0-9a-f]{40}", commit):
            raise gl.UserError("Invalid review identifiers")
        if checklist_id not in self.checklists or commit not in self.approved:
            raise gl.UserError("Checklist or snapshot is not registered")
        key = f"{checklist_id}:{part}:{commit}"
        if key in self.decisions:
            raise gl.UserError("Review already recorded")
        checklist = json.loads(self.checklists[checklist_id])
        expected_hash = self.approved[commit]
        url = EVIDENCE_ROOT + commit + "/evidence/ti-accuracy.json"

        def retrieve():
            response = gl.nondet.web.get(url)
            if not 1 <= len(response.body) <= 12_000:
                raise gl.UserError("Snapshot unavailable")
            if digest(response.body) != expected_hash:
                raise gl.UserError("Snapshot hash mismatch")
            try:
                return encode(extract(response.body, part))
            except (KeyError, ValueError, TypeError, gl.UserError):
                raise gl.UserError("Snapshot has no valid evidence for this part")

        evidence = json.loads(gl.eq_principle.strict_eq(retrieve))
        decision = {"checklist_id": checklist_id, "checklist_sha256": digest(encode(checklist).encode()),
                    "part": part, "commit": commit, "evidence_sha256": expected_hash, "profile": PROFILE,
                    "source": evidence["source"], "revision": evidence["revision"],
                    "requirements": assess(checklist["requirements"], evidence["rows"])}
        decision["decision_sha256"] = digest(encode(decision).encode())
        self.decisions[key] = encode(decision)

    @gl.public.view
    def get_checklist(self, checklist_id: str) -> str:
        return self.checklists[checklist_id] if checklist_id in self.checklists else ""

    @gl.public.view
    def get_review(self, checklist_id: str, part: str, commit: str) -> str:
        key = f"{checklist_id}:{part}:{commit}"
        return self.decisions[key] if key in self.decisions else ""
