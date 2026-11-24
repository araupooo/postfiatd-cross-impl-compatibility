# Claim-to-evidence index

Every claim in this pack, its status, and the exact evidence for it.
Status meanings: VERIFIED — read from the pinned sources with a
grep-verified file:line citation on both sides; SPECIFIED — stated in
the cited public documentation and cross-checked against code;
MODELLED — an output of the deterministic differential simulator on
the stated inputs; UNTESTABLE — not decidable from the pinned sources
alone.

| Claim | Status | Claim | Evidence |
| --- | --- | --- | --- |
| C-01 | VERIFIED | postfiatd requires 67% consensus agreement; rippled requires 80%. | R-03, R-04, E01, E02: `ConsensusParms.h:79`, `ValidatorList.cpp:1897-1900`. |
| C-02 | VERIFIED | The post-fix amendment majority is 67/100 in postfiatd and 80/100 in rippled. | R-05, E03: `SystemParameters.h:85`. |
| C-03 | VERIFIED | Close-time offset is a weighted median in postfiatd and an arithmetic mean in rippled. | R-06, E04: `RCLConsensus.cpp:709-728` vs rippled `:704-728`. |
| C-04 | VERIFIED | Among close times tied for the most votes, the earliest wins in postfiatd and the latest wins in rippled. | R-07, E05: `Consensus.h:1602-1613` vs rippled `:1605-1616`. |
| C-05 | VERIFIED | Pause-phase thresholds are 67/75/83/92% in postfiatd and 80/85/90/95% in rippled. | R-08, E06: `Consensus.h:1283-1294`. |
| C-06 | VERIFIED | Peer validations must arrive in canonical field order in postfiatd; rippled imposes no order requirement. | R-10, E08: `STValidation.h:59-92`. |
| C-07 | VERIFIED | Validations carry exclusion fields sfExclusionAdd and sfExclusionRemove in postfiatd; rippled has no such fields. | R-12, E10: `STValidation.cpp:78-88`. |
| C-08 | VERIFIED | Trusted validations are recorded as votes with the validation signing hash as proof in postfiatd; rippled records no vote. | R-13, E11: `RCLValidations.cpp:193-226`. |
| C-09 | VERIFIED | Unlisted validator manifests are capped at 1,000 in postfiatd with the oldest evicted; rippled keeps them unbounded. | R-15, E13: `Manifest.h:246-290`. |
| C-10 | VERIFIED | Networks 2025 and 2026 use the PostFiat genesis account r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA; rippled derives the genesis account from masterpassphrase (rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh). | R-19, E15: `Ledger.cpp:180-205` vs rippled `:180-186`. |
| C-11 | VERIFIED | The earliest ledger sequence is 1 in postfiatd and 32,570 in rippled. | R-20, E17: `SystemParameters.h:70-76`. |
| C-12 | VERIFIED | Ledger-replay responses return a three-way status (Ok, BadData, Malformed) and charge feeMalformedData (2,000) in postfiatd; rippled returns a bool and charges nothing. | R-24, E22: `LedgerReplayMsgHandler.h:27-80`. |
| C-13 | VERIFIED | ttVALIDATOR_VOTE (1501) and ltVALIDATOR_VOTE_STATS (0x008A) exist only in postfiatd. | R-31, R-32, E28, E29: `transactions.macro:1131-1150`, `ledger_entries.macro:510-530`. |
| C-14 | VERIFIED | Transactor preflight1 rejects transactions from excluded senders (temBAD_SRC_ACCOUNT) and to excluded destinations (temINVALID_ACCOUNT_ID) in postfiatd; rippled has no exclusion check. | R-34, E31: `Transactor.cpp:190-215`. |
| C-15 | VERIFIED | 36 amendments flipped from DefaultNo to DefaultYes in postfiatd, so a fresh network enables them by default where rippled does not. | R-38, E35: `features.macro:47-100` (64 DefaultYes in postfiatd vs 28 in rippled). |
| C-16 | VERIFIED | Ledger balance arithmetic uses overflow-checked add/subtract in postfiatd, and payment-strand sums that overflow end the strand as tecPATH_DRY; rippled adds unchecked. | R-39, R-40, E36, E38: `MathUtilities.h:26-60`, `Steps.h:526-575`. |
| C-17 | SPECIFIED | The rippled reference base is 3.1.2: postfiatd's own merge analysis records 21 upstream commits from 3.0.0 to 3.1.2, and the rippled tag points at commit 3ba3fcff (2026-03-12). | R-01, R-02, `docs/citations.md` S-01/S-02: merge analysis and rippled 3.1.2 tag, 24 Nov 2026. |
| C-18 | SPECIFIED | The XRP Ledger consensus protocol requires over 80% of trusted validators to collude to confirm an invalid transaction, and makes progress while fewer than 20% are faulty. | R-18, `docs/citations.md` S-03: XRPL consensus-protocol documentation, 24 Nov 2026. |
| C-19 | MODELLED | A 67% quorum lets a network validate with fewer agreeing validators, so the tolerated Byzantine share rises from 20% to 33% of the UNL. | R-17; threshold table; scenario S-01; `outputs/derived/cross-impl-results.json`. |
| C-20 | MODELLED | A validation carrying exclusion fields fails deserialization on a rippled peer (unknown field), so exclusion votes do not propagate to rippled nodes. | R-45; scenario S-08 run A (incompatible); `outputs/derived/cross-impl-results.json`. |
| C-21 | MODELLED | A ledger with 70 of 100 validators agreeing validates on postfiatd and not on rippled. | R-03, R-04; scenario S-01 run A (diverged); `outputs/derived/cross-impl-results.json`. |
| C-22 | MODELLED | One peer 120 seconds off moves the rippled close-time mean by 11 seconds and the postfiatd weighted median by 0 seconds. | R-06; scenario S-03 run A (diverged); `outputs/derived/cross-impl-results.json`. |
| C-23 | UNTESTABLE | Whether a mixed postfiatd/rippled network reaches consensus on a ledger containing ttVALIDATOR_VOTE transactions can only be settled by running both implementations together. | R-30; gap G-01. |
| C-24 | UNTESTABLE | Live-network close-time behavior under real clock skew is not decidable from static source: the model covers static inputs only. | R-06; gap G-07. |
