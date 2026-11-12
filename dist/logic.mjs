export function assess(checklist, rows) {
  return checklist.map(([label, low, high, limit]) => {
    const edges = [...new Set([low, high, ...rows.flatMap(row => row.slice(0, 2)).filter(t => low < t && t < high)])].sort((a, b) => a - b);
    const gaps = [];
    const citations = new Set();
    let worst = null;
    for (let i = 1; i < edges.length; i++) {
      const left = edges[i - 1];
      const right = edges[i];
      const matches = rows.filter(([a, b]) => a <= left && b >= right);
      matches.sort((a, b) => a[2] - b[2] || (a[3] < b[3] ? -1 : Number(a[3] > b[3])));
      if (!matches.length) {
        gaps.push([left, right]);
        continue;
      }
      const [, , amount, cite] = matches[0];
      citations.add(cite);
      worst = Math.max(worst ?? amount, amount);
    }
    return { label, range_C: [low, high], max_mC: limit, guarantee_mC: gaps.length ? null : worst,
      status: gaps.length ? "UNVERIFIED" : worst <= limit ? "MET" : "FAILED",
      citations: [...citations].sort(), uncovered_C: gaps };
  });
}

export function receiptOutcome(receipt) {
  const status = String(receipt.statusName ?? receipt.status ?? "UNKNOWN").toUpperCase();
  const result = String(receipt.txExecutionResultName ?? receipt.txExecutionResult ??
    receipt.consensus_data?.leader_receipt?.execution_result ?? "").toUpperCase();
  if (["CANCELED", "CANCELLED", "UNDETERMINED"].includes(status)) return { phase: "failed", status, result };
  if (status !== "FINALIZED" && status !== "7") return { phase: "pending", status, result };
  if (["SUCCESS", "FINISHED_WITH_RETURN"].includes(result)) return { phase: "success", status, result };
  return { phase: result ? "failed" : "unverified", status, result };
}
