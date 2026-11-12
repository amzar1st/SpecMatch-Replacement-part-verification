import { assess, receiptOutcome } from "./logic.mjs";
import { deployment } from "./config.mjs";
const parts = ["TMP117", "TMP116"];
const presets = {
  wide: [["Cold-start accuracy", -15, 45, 200], ["Indoor accuracy", 0, 45, 200], ["Extended range accuracy", -60, 45, 200]],
  narrow: [["Indoor accuracy", 0, 45, 200]],
  gap: [["Extended range accuracy", -60, 45, 200]],
};
const field = id => document.getElementById(id);
field("address").value = deployment.address;
field("checklist").value = deployment.checklist;
field("commit").value = deployment.commit;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
function temperature(value) {
  return `±${(value / 1000).toFixed(3).replace(/0$/, "")} °C`;
}
function render(records, live) {
  field("mode").textContent = live ? "Finalized Studionet state" : "Datasheet preview · local calculation";
  field("results").replaceChildren(...parts.map((part, index) => {
    const record = records[index];
    const article = node("article", undefined, "card");
    const head = node("header");
    head.append(node("h3", part), node("span", record?.revision ?? "No finalized review"));
    article.append(head);
    if (!record) return article;
    for (const row of record.requirements) {
      const section = node("div", undefined, "requirement");
      section.append(node("strong", row.label), node("p", `${row.range_C.join(" to ")} °C · Required ${temperature(row.max_mC)}`));
      section.append(node("span", row.status, `status ${row.status.toLowerCase()}`));
      if (row.guarantee_mC !== null) section.append(node("p", `Datasheet guarantee ${temperature(row.guarantee_mC)}`));
      if (row.uncovered_C.length) section.append(node("p", `Uncovered: ${row.uncovered_C.map(x => x.join(" to ")).join(", ")} °C`));
      if (row.citations.length) {
        const list = node("ul");
        list.append(...row.citations.map(cite => node("li", cite)));
        section.append(list);
      }
      article.append(section);
    }
    if (/^https:\/\/www\.ti\.com\/lit\/ds\//.test(record.source)) {
      const source = node("a", "Manufacturer datasheet ↗");
      source.href = record.source;
      article.append(source);
    }
    if (live) {
      const proof = node("details");
      proof.append(node("summary", "Decision and evidence hashes"), node("p", record.decision_sha256), node("p", record.evidence_sha256));
      proof.style.overflowWrap = "anywhere";
      article.append(proof);
    }
    return article;
  }));
}

let evidence;
let displayVersion = 0;
async function showPreview() {
  const version = ++displayVersion;
  try {
    const response = await fetch("./ti-accuracy.json");
    if (!response.ok) throw new Error("Evidence snapshot unavailable");
    evidence ??= await response.json();
    if (version !== displayVersion) return;
    render(parts.map(part => {
      const source = evidence.parts[part];
      return { ...source, requirements: assess(presets[field("preset").value],
        source.rows.map(([a, b, amount, unit, cite]) => [a, b, unit === "cC" ? amount * 10 : amount, cite])) };
    }), false);
  } catch (error) {
    if (version === displayVersion) field("mode").textContent = error.message;
  }
}
let clientPromise;
function connect() {
  clientPromise ??= Promise.all([
    import("https://cdn.jsdelivr.net/npm/genlayer-js@1.1.8/+esm"),
    import("https://cdn.jsdelivr.net/npm/genlayer-js@1.1.8/chains/+esm"),
    import("https://cdn.jsdelivr.net/npm/genlayer-js@1.1.8/types/+esm"),
  ]).then(([sdk, chains, types]) => ({
    client: sdk.createClient({chain: chains.studionet}), types,
  })).catch(error => { clientPromise = null; throw error; });
  return clientPromise;
}
function operation(id, callback) {
  field(id).addEventListener("submit", async event => {
    event.preventDefault();
    const button = event.submitter ?? field(id).querySelector("button");
    button.disabled = true;
    try { await callback(); }
    catch (error) { field("chain-status").textContent = error.message; }
    finally { button.disabled = false; }
  });
}
operation("read", async () => {
  const version = ++displayVersion;
  field("chain-status").textContent = "Reading finalized Studionet state…";
  const {client, types} = await connect();
  const address = field("address").value;
  const checklist = field("checklist").value;
  const commit = field("commit").value;
  const values = await Promise.all(parts.map(part => client.readContract({address, functionName: "get_review",
    args: [checklist, part, commit], transactionHashVariant: types.TransactionHashVariant.LATEST_FINAL })));
  if (version !== displayVersion) return;
  render(values.map(value => value ? JSON.parse(value) : null), true);
  field("chain-status").textContent = values.some(Boolean) ? "Loaded finalized contract records." : "No finalized reviews for this checklist and evidence commit.";
});
operation("track", async () => {
  const hash = field("hash").value;
  field("chain-status").textContent = "Checking transaction…";
  const {client} = await connect();
  for (let i = 0; i < 15; i++) {
    let receipt;
    try { receipt = await client.getTransaction({hash}); }
    catch (error) { field("chain-status").textContent = `Receipt unavailable. Keep this hash and retry: ${hash} (${error.message})`; return; }
    const {phase, status, result} = receiptOutcome(receipt);
    field("chain-status").textContent = `${phase}: ${status}${result ? ` / ${result}` : ""} · ${hash}`;
    if (phase !== "pending") return;
    await new Promise(resolve => setTimeout(resolve, 4000));
  }
  field("chain-status").textContent = `Still pending. Track the same hash again: ${hash}`;
});
field("preset").addEventListener("change", showPreview);
if (deployment.address) showPreview().then(() => field("read").requestSubmit());
else showPreview();
