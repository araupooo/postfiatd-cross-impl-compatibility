# Scenario matrix

Deterministic outputs of `src/cross_impl_model.py` on
`configs/scenarios.json`. Each run feeds the same input to a
postfiatd-rule path and a rippled-rule path. matched: both produce the
same result. diverged: different results for the same input (both
still function). degraded: one side handles the input safely while
the other degrades (unsafe behavior or unbounded growth).
incompatible: the input is valid on one side and unrepresentable on
the other (unknown transaction type or unknown field). Rounds: 1 for
every run — each differential decision is a single-round computation.

| Scenario | Run | Kind | postfiatd | rippled 3.1.2 | Outcome | Reason | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S-01 | A | quorum | validates=True (quorum 67) | validates=False (quorum 80) | diverged | different_result_same_input | 1 |
| S-01 | B | quorum | validates=True (quorum 67) | validates=True (quorum 80) | matched | same_result_both_implementations | 1 |
| S-02 | A | amendment | enables=True (67%) | enables=False (80%) | diverged | different_result_same_input | 1 |
| S-02 | B | amendment | enables=True (67%) | enables=True (80%) | matched | same_result_both_implementations | 1 |
| S-03 | A | close_offset | offset 0 s (weighted_median) | offset 11 s (arithmetic_mean) | diverged | different_result_same_input | 1 |
| S-03 | B | close_offset | offset 0 s (weighted_median) | offset 0 s (arithmetic_mean) | matched | same_result_both_implementations | 1 |
| S-04 | A | tie_break | close 1000 (earliest_wins) | close 1005 (latest_wins) | diverged | different_result_same_input | 1 |
| S-05 | A | pause_phase | pauses=False (phase-0 67%) | pauses=True (phase-0 80%) | diverged | different_result_same_input | 1 |
| S-05 | B | pause_phase | pauses=False (phase-0 67%) | pauses=False (phase-0 80%) | matched | same_result_both_implementations | 1 |
| S-06 | A | pseudo_tx | applied_creates_vote_stats | rejected_unknown_tx_type | incompatible | unrepresentable_on_rippled | 1 |
| S-07 | A | exclusion | rejected_at_preflight | applies_normally | diverged | different_result_same_input | 1 |
| S-08 | A | validation_fields | vote_recorded_with_exclusion | deserialization_fails_unknown_field | incompatible | unrepresentable_on_rippled | 1 |
| S-09 | A | genesis | r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA | rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh | diverged | different_result_same_input | 1 |
| S-09 | B | genesis | rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh | rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh | matched | same_result_both_implementations | 1 |
| S-10 | A | shamap_depth | clamped_to_leaf_depth | unsafe_out_of_range | degraded | rippled_side_degrades | 1 |
| S-11 | A | payment_overflow | tecPATH_DRY | wraps_silently | diverged | different_result_same_input | 1 |
| S-12 | A | json_array | rejected_array_too_big | accepted | diverged | different_result_same_input | 1 |
| S-13 | A | manifest_flood | keeps 1000 (cap 1000) | keeps 1500 (unbounded) | degraded | rippled_side_degrades | 1 |

Totals: 13 scenarios, 18 runs — matched 5, diverged 9, degraded 2,
incompatible 2.

## Quorum threshold table

Validator quorum is max(ceil(UNL * pct / 100), ceil(UNL * 60 / 100)),
pct 67 in postfiatd and 80 in rippled
(`ValidatorList.cpp:1897-1934` vs rippled `:1884-1918`). Tolerated
Byzantine validators = UNL size minus quorum.

| UNL size | Quorum (postfiatd) | Quorum (rippled) | Tolerated Byzantine (postfiatd) | Tolerated Byzantine (rippled) |
| --- | --- | --- | --- | --- |
| 3 | 3 | 3 | 0 | 0 |
| 4 | 3 | 4 | 1 | 0 |
| 7 | 5 | 6 | 2 | 1 |
| 10 | 7 | 8 | 3 | 2 |
| 21 | 15 | 17 | 6 | 4 |
| 35 | 24 | 28 | 11 | 7 |
| 100 | 67 | 80 | 33 | 20 |

Note the UNL-3 row: both implementations need all 3 validators, so
the quorum divergence vanishes at the smallest UNL size.

## Constants comparison table

| Item | postfiatd | rippled 3.1.2 | Class |
| --- | --- | --- | --- |
| consensus quorum (minCONSENSUS_PCT) | 67 | 80 | DIVERGE |
| amendment majority (post-fix) | 67/100 | 80/100 | DIVERGE |
| close-time offset method | weighted median | arithmetic mean | DIVERGE |
| close-time tie-break | earliest wins | latest wins | DIVERGE |
| pause phase thresholds | 67/75/83/92 | 80/85/90/95 | DIVERGE |
| genesis account (networks 2025/2026) | r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA | rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh | DIVERGE |
| earliest ledger sequence | 1 | 32570 | DIVERGE |
| system name | postfiat | ripple | DIVERGE |
| untrusted manifest cap | 1000 | unbounded | DIVERGE |
| exclusion list maximum | 100 | none | DIVERGE |
| JSON array element cap | 512 | none | DIVERGE |
| JSON nesting depth cap | 64 | 64 | MATCH |
| variable-length field maximum | 918744 | 918744 | MATCH |
| disputed-transaction stall test | parameterized by minCONSENSUS_PCT | parameterized by minCONSENSUS_PCT | MATCH |
| amendment majority timestamp | parentCloseTime | parentCloseTime | MATCH |
| fee escalation | quadratic | quadratic | MATCH |
| load-fee tracking | identical | identical | MATCH |
| validator vote transaction type | ttVALIDATOR_VOTE (1501) | absent | DIVERGE |
| validator vote stats ledger entry | ltVALIDATOR_VOTE_STATS (0x008A) | absent | DIVERGE |
