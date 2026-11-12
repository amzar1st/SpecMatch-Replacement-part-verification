# Project Explorer submission

- **Contribution type** — Builder → Projects
- **Project name** — SpecMatch
- **Suggested tags** — Developer Tools, Oracles, Real-World Data. Select the closest labels in the form.
- **One-liner** — Verify replacement sensors against a locked buyer checklist using GenLayer consensus and cited manufacturer datasheet limits.
- **Frontend** — https://specmatch-replacement-parts.tinymule33.chatgpt.site
- **Repository** — https://github.com/amzar1st/SpecMatch-Replacement-part-verification
- **Contract** — https://explorer-studio.genlayer.com/address/0x93471961afD172Fe0f32bd1Cde93cD8c327992A3
- **Live evidence** — https://github.com/amzar1st/SpecMatch-Replacement-part-verification/blob/main/docs/LIVE_VERIFICATION.md

## Overview

SpecMatch helps procurement teams evaluate replacement temperature sensors against a buyer’s immutable accuracy checklist. GenLayer validators independently fetch a revision-labeled datasheet transcription pinned to a Git commit and SHA-256, then agree on the cited rows for the exact model. The Intelligent Contract normalizes the units, checks the guaranteed error across the full temperature interval, and records MET, FAILED, or UNVERIFIED for each requirement. The Studio demo compares two Texas Instruments sensors and shows how a headline ±0.20 °C guarantee can fail a cold-start requirement once its specified temperature range is applied. The dashboard reads finalized decisions and lets reviewers inspect the source citations and transaction lifecycle.
