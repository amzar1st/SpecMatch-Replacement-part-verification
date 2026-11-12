import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { assess, receiptOutcome } from "../dist/logic.mjs";

const evidence = JSON.parse(readFileSync(new URL("../dist/ti-accuracy.json", import.meta.url)));
const normalized = part => evidence.parts[part].rows.map(([a,b,n,u,cite]) => [a,b,u === "cC" ? n * 10 : n,cite]);
const rules = [["Cold-start", -15, 45, 200], ["Indoor", 0, 45, 200], ["Gap", -60, 45, 200]];

test("browser preview distinguishes the narrow guarantee from the full interval", () => {
  assert.deepEqual(assess(rules, normalized("TMP117")).map(row => row.status), ["MET", "MET", "UNVERIFIED"]);
  assert.deepEqual(assess(rules, normalized("TMP116")).map(row => row.status), ["FAILED", "MET", "UNVERIFIED"]);
});

test("receipt processing distinguishes pending, successful, failed and unknown outcomes", () => {
  assert.equal(receiptOutcome({statusName: "ACCEPTED", txExecutionResultName: "SUCCESS"}).phase, "pending");
  assert.equal(receiptOutcome({statusName: "FINALIZED", txExecutionResultName: "SUCCESS"}).phase, "success");
  assert.equal(receiptOutcome({statusName: "FINALIZED", txExecutionResultName: "USER_ERROR"}).phase, "failed");
  assert.equal(receiptOutcome({statusName: "UNDETERMINED"}).phase, "failed");
  assert.equal(receiptOutcome({statusName: "FINALIZED"}).phase, "unverified");
});
