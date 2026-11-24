#!/usr/bin/env python3
"""cross_impl_model.py — deterministic differential model: postfiatd vs rippled 3.1.2.

Usage:
    python3 src/cross_impl_model.py [--help]

Reads configs/scenarios.json and writes:
    outputs/derived/cross-impl-results.json
    outputs/derived/scenario-matrix.json

Each scenario run feeds the same input to a postfiatd-rule path and a
rippled-rule path and reports whether the two implementations agree.
Every number comes from the scenario inputs plus the pinned-code
constants in configs/scenarios.json (67% vs 80% consensus quorum and
amendment majority; 60% absolute-minimum quorum; 1,000 untrusted
manifest cap; 100-address exclusion cap; 512-element JSON array cap;
64 JSON depth cap; 918,744 maximum variable-length field size; 2,000
malformed-data charge; earliest ledger sequence 1 vs 32,570; SHAMap
leaf depth 64; validator-vote type 1501). No live node is involved,
no timestamps are recorded, and no wall-clock time is measured:
re-running produces byte-identical outputs.

Differential math (mirrors the pinned code, integer arithmetic):
  - validator quorum: max(ceil(unl * pct / 100), ceil(unl * 60 / 100)),
    pct 67 in postfiatd (ValidatorList.cpp:1897-1934) and 80 in rippled
    (ValidatorList.cpp:1884-1918). Ceilings use integer arithmetic:
    (n * p + 99) // 100.
  - amendment majority: 67/100 vs 80/100
    (SystemParameters.h:85 on both sides).
  - close-time offset: postfiatd takes the lower weighted median of
    the peers' close times (ConsensusTypes.h medianCloseOffset);
    rippled takes the arithmetic mean, rounded to nearest
    (RCLConsensus.cpp:704-728: total += count / 2, then total /= count).
  - close-time tie-break: both walk the vote bins and keep the last
    bin whose votes reach the running threshold; postfiatd walks
    highest-time first so the earliest wins among ties, rippled walks
    lowest-time first so the latest wins (Consensus.h:1602-1613 vs
    :1605-1616).
  - pause phases: postfiatd waits while fewer than 67% of validators
    moved on, rippled while fewer than 80% (Consensus.h:1283-1294).
  - genesis account: postfiatd uses r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA
    for network IDs 2025/2026 outside standalone mode, and the
    masterpassphrase-derived account otherwise; rippled always derives
    from masterpassphrase (Ledger.cpp:180-205 vs :180-186).
  - SHAMap node-ID depth: postfiatd clamps a depth past the leaf
    depth (64) to the leaf depth; rippled indexes out of range
    (SHAMapNodeID.cpp:57-75 vs :57-66).
  - payment strand sums: postfiatd adds with checkedAdd and ends the
    strand as tecPATH_DRY on overflow; rippled accumulates unchecked
    (Steps.h:526-575, BookStep.cpp:1006-1016).
  - JSON arrays: postfiatd rejects any field over 512 elements;
    rippled has no array cap (STParsedJSON.h:29-34).
  - manifest flood: postfiatd keeps at most 1,000 unlisted manifests,
    evicting the oldest; rippled keeps all of them (Manifest.h:246-290).

Outcome classes:
  - matched: both implementations produce the same result.
  - diverged: the two implementations produce different results for
    the same input (both still function).
  - degraded: one side handles the input safely while the other
    degrades (unsafe behavior or unbounded growth).
  - incompatible: the input is valid on one side and unrepresentable
    on the other (unknown transaction type or unknown field).
"""
import json
import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parent.parent
PINNED_COMMIT = "0085a1ff885d6a446369cf73a4430f75af22be55"
RIPPLED_COMMIT = "3ba3fcff4c4898a96a57838bb7c67a44a3d2ec5c"
INT64_MAX = 9223372036854775807


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def ceil_pct(n, pct):
    """ceil(n * pct / 100) with exact integer arithmetic."""
    return (n * pct + 99) // 100


def quorum_needed(total, pct):
    """ValidatorList::calculateQuorum without the unavailable-publisher branch."""
    return max(ceil_pct(total, pct), ceil_pct(total, 60))


def weighted_median_offset(self_time, peer_times):
    """Lower weighted median of close times minus self (postfiatd)."""
    total_weight = 1 + sum(w for _, w in peer_times)
    half = (total_weight + 1) // 2
    tally = 0
    median = None
    self_placed = False
    for t, w in sorted(peer_times):
        if not self_placed and self_time <= t:
            self_placed = True
            tally += 1
            if tally >= half:
                median = self_time
                break
        tally += w
        if tally >= half:
            median = t
            break
    if median is None:
        median = self_time
    return median - self_time


def mean_offset(self_time, peer_times):
    """Arithmetic mean of close times minus self, rounded to nearest (rippled)."""
    total = self_time
    count = 1
    for t, w in peer_times:
        total += t * w
        count += w
    total += count // 2
    total //= count
    return total - self_time


def tie_break_winner(bins, threshold, reverse):
    """Walk the bins and keep the last one reaching the running threshold."""
    ordered = sorted(bins, reverse=reverse)
    thresh = threshold
    winner = None
    for t, v in ordered:
        if v >= thresh:
            winner = t
            thresh = v
    return winner


def checked_add(a, b):
    """int64 checked add: None on overflow."""
    s = a + b
    if s > INT64_MAX or s < -9223372036854775808:
        return None
    return s


def wrap_int64(n):
    """Two's-complement wrap of an integer into int64 range."""
    return ((n + 2 ** 63) % 2 ** 64) - 2 ** 63


def simulate_run(scenario, run, consts):
    p = run["params"]
    kind = run["kind"]
    events = [{"round": ev["round"], "text": ev["text"]}
              for ev in run["events"]]
    pf = {}
    rp = {}
    # cmp_* hold the comparable behavioral outcome; method labels and
    # thresholds are recorded in pf/rp but never decide matched/diverged.
    cmp_pf = cmp_rp = None

    if kind == "quorum":
        total, agreeing = p["validators_total"], p["validators_agreeing"]
        q_pf = quorum_needed(total, 67)
        q_r = quorum_needed(total, 80)
        pf = {"quorum_needed": q_pf, "validates": agreeing >= q_pf}
        rp = {"quorum_needed": q_r, "validates": agreeing >= q_r}
        cmp_pf, cmp_rp = pf["validates"], rp["validates"]
        events.append({"round": 1, "text": (
            f"quorum needed: postfiatd {q_pf}, rippled {q_r}; "
            f"{agreeing} agreeing validates on "
            f"{'both' if pf['validates'] == rp['validates'] else 'postfiatd only'}")})
    elif kind == "amendment":
        pct = p["votes_for_pct"]
        pf = {"enables": pct >= 67, "majority_pct": 67}
        rp = {"enables": pct >= 80, "majority_pct": 80}
        cmp_pf, cmp_rp = pf["enables"], rp["enables"]
        events.append({"round": 1, "text": (
            f"{pct}% support over {p['weeks']} weeks: postfiatd "
            f"{'enables' if pf['enables'] else 'does not enable'} the amendment, "
            f"rippled {'enables' if rp['enables'] else 'does not enable'} it")})
    elif kind == "close_offset":
        self_time = p["self_time"]
        peers = [tuple(x) for x in p["peer_times"]]
        off_pf = weighted_median_offset(self_time, peers)
        off_r = mean_offset(self_time, peers)
        pf = {"offset_seconds": off_pf, "method": "weighted_median"}
        rp = {"offset_seconds": off_r, "method": "arithmetic_mean"}
        cmp_pf, cmp_rp = off_pf, off_r
        events.append({"round": 1, "text": (
            f"close-time offset: postfiatd {off_pf} s (weighted median), "
            f"rippled {off_r} s (arithmetic mean)")})
    elif kind == "tie_break":
        bins = [tuple(x) for x in p["bins"]]
        w_pf = tie_break_winner(bins, p["threshold"], reverse=True)
        w_r = tie_break_winner(bins, p["threshold"], reverse=False)
        pf = {"consensus_close_time": w_pf, "tie_break": "earliest_wins"}
        rp = {"consensus_close_time": w_r, "tie_break": "latest_wins"}
        cmp_pf, cmp_rp = w_pf, w_r
        events.append({"round": 1, "text": (
            f"tied bins {p['bins']}: postfiatd picks {w_pf} (earliest), "
            f"rippled picks {w_r} (latest)")})
    elif kind == "pause_phase":
        pct = p["validators_moved_on_pct"]
        pf = {"pauses": pct < 67, "phase0_threshold": 67}
        rp = {"pauses": pct < 80, "phase0_threshold": 80}
        cmp_pf, cmp_rp = pf["pauses"], rp["pauses"]
        events.append({"round": 1, "text": (
            f"{pct}% moved on: postfiatd {'pauses' if pf['pauses'] else 'proceeds'} "
            f"(phase-0 threshold 67%), rippled "
            f"{'pauses' if rp['pauses'] else 'proceeds'} (phase-0 threshold 80%)")})
    elif kind == "pseudo_tx":
        pf = {"result": "applied_creates_vote_stats", "tx_type": p["tx_type"]}
        rp = {"result": "rejected_unknown_tx_type", "tx_type": p["tx_type"]}
        cmp_pf, cmp_rp = pf["result"], rp["result"]
        events.append({"round": 1, "text": (
            f"{p['tx_type']} is applied by postfiatd (creates ltVALIDATOR_VOTE_STATS) "
            f"and rejected by rippled as an unknown transaction type")})
    elif kind == "exclusion":
        code = "temBAD_SRC_ACCOUNT" if p["tx_direction"] == "source" else "temINVALID_ACCOUNT_ID"
        pf = {"result": "rejected_at_preflight", "code": code}
        rp = {"result": "applies_normally", "code": None}
        cmp_pf, cmp_rp = pf["result"], rp["result"]
        events.append({"round": 1, "text": (
            f"excluded {p['tx_direction']} account: postfiatd rejects at preflight1 "
            f"({code}); rippled applies the transaction normally")})
    elif kind == "validation_fields":
        pf = {"result": "vote_recorded_with_exclusion"}
        rp = {"result": "deserialization_fails_unknown_field"}
        cmp_pf, cmp_rp = pf["result"], rp["result"]
        events.append({"round": 1, "text": (
            "postfiatd records the vote and the exclusion change; rippled fails "
            "to deserialize the validation (unknown field sfExclusionAdd)")})
    elif kind == "genesis":
        if p["network_id"] in (2025, 2026) and not p["standalone"]:
            pf_acct = "r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA"
        else:
            pf_acct = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
        rp_acct = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
        pf = {"genesis_account": pf_acct}
        rp = {"genesis_account": rp_acct}
        cmp_pf, cmp_rp = pf_acct, rp_acct
        events.append({"round": 1, "text": (
            f"genesis account: postfiatd {pf_acct}, rippled {rp_acct}")})
    elif kind == "shamap_depth":
        depth, leaf = p["depth"], p["leaf_depth"]
        pf = {"result": "clamped_to_leaf_depth" if depth > leaf else "accepted",
              "effective_depth": min(depth, leaf)}
        rp = {"result": "unsafe_out_of_range" if depth > leaf else "accepted",
              "effective_depth": depth}
        cmp_pf, cmp_rp = pf["result"], rp["result"]
        events.append({"round": 1, "text": (
            f"node ID depth {depth} (leaf depth {leaf}): postfiatd clamps to "
            f"{min(depth, leaf)} and continues; rippled indexes out of range")})
    elif kind == "payment_overflow":
        amounts = p["amounts"]
        total = 0
        overflow = False
        for a in amounts:
            nxt = checked_add(total, a)
            if nxt is None:
                overflow = True
                break
            total = nxt
        pf = {"result": "tecPATH_DRY" if overflow else "sum_ok",
              "sum": None if overflow else total}
        rp = {"result": "wraps_silently" if overflow else "sum_ok",
              "sum": wrap_int64(sum(amounts)) if overflow else sum(amounts)}
        cmp_pf, cmp_rp = pf["result"], rp["result"]
        events.append({"round": 1, "text": (
            f"strand amounts {amounts}: postfiatd ends the strand as tecPATH_DRY "
            f"on overflow; rippled wraps to {rp['sum']}")})
    elif kind == "json_array":
        size = p["array_size"]
        pf = {"result": "rejected_array_too_big" if size > 512 else "accepted"}
        rp = {"result": "accepted"}
        cmp_pf, cmp_rp = pf["result"], rp["result"]
        events.append({"round": 1, "text": (
            f"array of {size} elements: postfiatd rejects (cap 512), "
            f"rippled accepts (no cap)")})
    elif kind == "manifest_flood":
        n = p["unlisted_manifests"]
        pf = {"kept": min(n, 1000), "cap": 1000}
        rp = {"kept": n, "cap": None}
        cmp_pf, cmp_rp = pf["kept"], rp["kept"]
        events.append({"round": 1, "text": (
            f"{n} unlisted manifests: postfiatd keeps {min(n, 1000)} "
            f"(oldest evicted), rippled keeps all {n} (unbounded)")})
    else:
        raise ValueError(f"unknown scenario kind: {kind}")

    if cmp_pf == cmp_rp:
        outcome, reason = "matched", "same_result_both_implementations"
    elif rp.get("result") in ("rejected_unknown_tx_type",
                              "deserialization_fails_unknown_field"):
        outcome, reason = "incompatible", "unrepresentable_on_rippled"
    elif rp.get("result") == "unsafe_out_of_range" or (
            kind == "manifest_flood" and p["unlisted_manifests"] > 1000):
        outcome, reason = "degraded", "rippled_side_degrades"
    else:
        outcome, reason = "diverged", "different_result_same_input"

    return {
        "label": run["label"],
        "title": run["title"],
        "kind": kind,
        "params": p,
        "postfiatd": pf,
        "rippled": rp,
        "outcome": outcome,
        "reason": reason,
        "rounds": 1,
        "events": events,
    }


def main():
    if "--help" in sys.argv[1:]:
        print(__doc__.strip())
        print("\nusage: python3 src/cross_impl_model.py [--help]")
        return 0
    sc = load_json(PACK_ROOT / "configs" / "scenarios.json")
    consts = sc["constants"]
    assert sc.get("pinned_commit") == PINNED_COMMIT, "scenarios pinned_commit mismatch"
    assert sc.get("rippled_commit") == RIPPLED_COMMIT, "scenarios rippled_commit mismatch"
    assert sc.get("schema_version") == 1, "scenarios schema_version != 1"

    results_scenarios = []
    matrix_rows = []
    totals = {"scenarios": 0, "runs": 0, "matched": 0, "diverged": 0,
              "degraded": 0, "incompatible": 0}
    for scenario in sc["scenarios"]:
        runs = [simulate_run(scenario, run, consts)
                for run in scenario["runs"]]
        results_scenarios.append({
            "id": scenario["id"],
            "title": scenario["title"],
            "runs": runs,
        })
        totals["scenarios"] += 1
        for run in runs:
            totals["runs"] += 1
            totals[run["outcome"]] += 1
            matrix_rows.append({
                "scenario": scenario["id"],
                "run": run["label"],
                "kind": run["kind"],
                "postfiatd": run["postfiatd"],
                "rippled": run["rippled"],
                "outcome": run["outcome"],
                "reason": run["reason"],
                "rounds": run["rounds"],
            })

    threshold_table = []
    for unl in (3, 4, 7, 10, 21, 35, 100):
        q_pf = quorum_needed(unl, 67)
        q_r = quorum_needed(unl, 80)
        threshold_table.append({
            "unl_size": unl,
            "quorum_postfiatd": q_pf,
            "quorum_rippled": q_r,
            "tolerated_byzantine_postfiatd": unl - q_pf,
            "tolerated_byzantine_rippled": unl - q_r,
        })

    constants_table = [
        {"item": "consensus quorum (minCONSENSUS_PCT)", "postfiatd": 67, "rippled": 80, "class": "DIVERGE"},
        {"item": "amendment majority (post-fix)", "postfiatd": "67/100", "rippled": "80/100", "class": "DIVERGE"},
        {"item": "close-time offset method", "postfiatd": "weighted median", "rippled": "arithmetic mean", "class": "DIVERGE"},
        {"item": "close-time tie-break", "postfiatd": "earliest wins", "rippled": "latest wins", "class": "DIVERGE"},
        {"item": "pause phase thresholds", "postfiatd": "67/75/83/92", "rippled": "80/85/90/95", "class": "DIVERGE"},
        {"item": "genesis account (networks 2025/2026)", "postfiatd": "r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA", "rippled": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh", "class": "DIVERGE"},
        {"item": "earliest ledger sequence", "postfiatd": 1, "rippled": 32570, "class": "DIVERGE"},
        {"item": "system name", "postfiatd": "postfiat", "rippled": "ripple", "class": "DIVERGE"},
        {"item": "untrusted manifest cap", "postfiatd": 1000, "rippled": "unbounded", "class": "DIVERGE"},
        {"item": "exclusion list maximum", "postfiatd": 100, "rippled": "none", "class": "DIVERGE"},
        {"item": "JSON array element cap", "postfiatd": 512, "rippled": "none", "class": "DIVERGE"},
        {"item": "JSON nesting depth cap", "postfiatd": 64, "rippled": 64, "class": "MATCH"},
        {"item": "variable-length field maximum", "postfiatd": 918744, "rippled": 918744, "class": "MATCH"},
        {"item": "disputed-transaction stall test", "postfiatd": "parameterized by minCONSENSUS_PCT", "rippled": "parameterized by minCONSENSUS_PCT", "class": "MATCH"},
        {"item": "amendment majority timestamp", "postfiatd": "parentCloseTime", "rippled": "parentCloseTime", "class": "MATCH"},
        {"item": "fee escalation", "postfiatd": "quadratic", "rippled": "quadratic", "class": "MATCH"},
        {"item": "load-fee tracking", "postfiatd": "identical", "rippled": "identical", "class": "MATCH"},
        {"item": "validator vote transaction type", "postfiatd": "ttVALIDATOR_VOTE (1501)", "rippled": "absent", "class": "DIVERGE"},
        {"item": "validator vote stats ledger entry", "postfiatd": "ltVALIDATOR_VOTE_STATS (0x008A)", "rippled": "absent", "class": "DIVERGE"},
    ]

    results = {
        "pack": "Cross-Implementation Compatibility: postfiatd vs rippled 3.1.2",
        "pinned_commit": PINNED_COMMIT,
        "rippled_commit": RIPPLED_COMMIT,
        "rippled_tag": "3.1.2",
        "constants": consts,
        "scenarios": results_scenarios,
        "totals": totals,
        "threshold_table": threshold_table,
        "constants_table": constants_table,
    }
    matrix = {"rows": matrix_rows, "totals": totals}

    outdir = PACK_ROOT / "outputs" / "derived"
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / "cross-impl-results.json", "w") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
        fh.write("\n")
    with open(outdir / "scenario-matrix.json", "w") as fh:
        json.dump(matrix, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"simulator: {totals['scenarios']} scenarios, {totals['runs']} runs")
    print(f"simulator: matched {totals['matched']}, diverged {totals['diverged']}, "
          f"degraded {totals['degraded']}, incompatible {totals['incompatible']}")
    print("simulator: wrote outputs/derived/cross-impl-results.json")
    print("simulator: wrote outputs/derived/scenario-matrix.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
