# Live verification

- Network: Studionet, chain ID 61999.
- [Contract address](https://explorer-studio.genlayer.com/address/0x93471961afD172Fe0f32bd1Cde93cD8c327992A3)
- Studio built-in signer: `0x62750Bb60A705B27B96867c60665D47cCF5B1Dd7`.
- [Pinned datasheet transcription](https://github.com/amzar1st/SpecMatch-Replacement-part-verification/blob/964b7e115b8ba21b928ac3905e8259752bec40e7/evidence/ti-accuracy.json)
- Evidence SHA-256: `8dce431969cb5b12b1f210d687bba9d0895bdb5c68e4f053e96525d5349a1cb4`.

| Action | Transaction | Studio status |
| --- | --- | --- |
| Deploy corrected SpecMatch | [Deployment receipt](https://explorer-studio.genlayer.com/tx/0x67101c240a5caa5bb78e728193931b0063c5dfad961f5f922a298b32642db2f9) | Finalized · SUCCESS |

The corrected instance currently has one transaction in the explorer. Live checklist and review receipts are pending. Earlier reviews on the superseded deployment finalized with an execution error because the hosted response object did not expose `status_code`. The corrected contract bounds the response body and verifies its SHA-256 before parsing.

## Reproduce in Studio

Use [Run and Debug](https://studio.genlayer.com/run-debug) and Normal (Full Consensus). The deployment uses the exact bytes of [the contract source](../contracts/spec_match.py). Select a built-in account and deploy with no constructor arguments when reproducing on a fresh instance.

Call `lock_checklist` with ID `cold-start` and the following string.

```json
[["Cold-start accuracy",-15,45,20,"cC"],["Indoor accuracy",0,45,200,"mC"],["Extended range accuracy",-60,45,200,"mC"]]
```

Call `review` with `cold-start`, `TMP117`, and the pinned commit above. Repeat with `TMP116`. Once each transaction is finalized, select **Finalized** in Read Methods and call `get_review` with the same arguments. The public dashboard uses the same finalized view.

Expected results from the local tests and datasheet preview.

| Requirement | TMP117 | TMP116 |
| --- | --- | --- |
| −15 to 45 °C, max ±0.20 °C | MET, ±0.10 °C | FAILED, ±0.25 °C |
| 0 to 45 °C, max ±0.20 °C | MET, ±0.10 °C | MET, ±0.20 °C |
| −60 to 45 °C, max ±0.20 °C | UNVERIFIED | UNVERIFIED |

The TMP116 accuracy rows in section 6.5 specify the applicable temperature and voltage ranges. Footnote 1 supplies the averaging and conversion conditions. The looser ±0.25 °C guarantee applies to the cold end of the checklist range.

## Automated verification

`python -m unittest discover -s tests -v` and `node --test tests/*.test.mjs` cover the verdicts, boundary segmentation, unit conversion, receipt state handling, authorization, duplicate prevention, malformed input, evidence mismatches, fetch errors, and retry behavior. The Python suite substitutes local storage, web responses, and the consensus runner. The linked receipt verifies the corrected constructor on Studionet.
