# SpecMatch

SpecMatch verifies whether a replacement digital temperature sensor meets a buyer's locked accuracy checklist over the entire operating interval. The demo compares TI's TMP117 and TMP116. A procurement summary can quote a headline accuracy while omitting the test conditions and the endpoints where that accuracy applies.

## Use the app

Open the [public dashboard](https://specmatch-replacement-parts.tinymule33.chatgpt.site). It loads finalized Studionet records by default and includes interactive previews for alternate temperature ranges. Each result shows the required limit, the applicable guarantee, missing coverage if any, and the manufacturer citation. Enter a Studio transaction hash in the tracker to see its status.

Write transactions are signed in [GenLayer Studio](https://studio.genlayer.com/run-debug) using its built-in account. The dashboard reads finalized state and observes transaction receipts. This keeps the Studio signing key on its own origin.

## How the contract works

1. The buyer locks a checklist containing 1–8 named accuracy requirements. A requirement is `[label, lowC, highC, maxError, unit]`. Accuracy accepts integer centidegrees (`cC`) or millidegrees (`mC`), and the contract normalizes to millidegrees. Temperature endpoints use whole degrees Celsius.
2. The curator approves a GitHub commit and SHA-256 for a structured datasheet transcription. The demo snapshot is seeded at deployment. Anyone can request a review against a locked checklist and approved snapshot.
3. GenLayer validators independently fetch the pinned snapshot, verify its SHA-256, and extract the model-specific, sorted evidence rows under strict equality. The contract calculates the tightest guaranteed error for each segment and uses the loosest segment guarantee across the requested interval.
4. The contract writes `MET` if complete coverage meets the threshold, `FAILED` if coverage is complete but the published bound is looser, and `UNVERIFIED` if any segment lacks coverage. Every record binds the checklist hash, evidence hash, source revision, citations, and the result hash. Repeated submissions for the same record key are rejected.

The first release covers maximum temperature error under the stated 3.3 V, eight-average, one-hertz test profile and cited datasheet conditions. The curator is responsible for checking the structured transcription against the original TI datasheet. Consensus verifies retrieval and extraction from the approved transcription. The review records published guarantees and leaves other compatibility requirements, including mechanical fit and pinout, outside the checklist.

## Verify locally

```sh
python -m unittest discover -s tests -v
node --test tests/*.test.mjs
python -m http.server 8000 --directory dist
```

Open http://localhost:8000 for the dashboard. See [live verification](docs/LIVE_VERIFICATION.md) for the Studio inputs, contract, and transaction evidence.
