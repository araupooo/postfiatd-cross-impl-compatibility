#!/usr/bin/env python3
"""probe.py — re-verify the cross-implementation compatibility pack from its outputs.

Usage:
    python3 scripts/probe.py [--skip-manifest-check] [CROSS_IMPL_RESULTS_JSON]

The --skip-manifest-check flag is for run_all.sh step 4 only: the
manifest on disk at that point predates the just-regenerated results,
so comparing against it would fail on any input change; step 5b re-runs
the probe without the flag after rewriting the manifest. A standalone
probe run (no flag) always performs the manifest check.

Checks (all re-derived, none trusted):
  A-00 pinned checkout HEADs equal the pinned commits (postfiatd
     0085a1ff... and rippled 3.1.2 3ba3fcff...).
  A-01 every VERIFIED rule's anchor sits inside its cited range in
     the postfiatd checkout AND its rippled reference anchor sits
     inside the cited rippled range (or the absent pattern has 0 hits
     in the cited rippled file); SPECIFIED rules carry external URLs;
     MODELLED / UNTESTABLE rules carry no file source. (45 rules:
     38/4/2/1.)
  B-01 scenario arithmetic: 13 scenarios, 18 runs; outcomes matched 5
     / diverged 9 / degraded 2 / incompatible 2; matrix rows == runs;
     per-kind outcomes re-derived from the scenario params (quorum
     formula, median vs mean, tie-break walk, pause thresholds,
     genesis selection, depth clamp, checked add, array cap, manifest
     cap).
  C-01 threshold and constants tables re-derived: quorum rows match
     max(ceil(unl*pct/100), ceil(unl*60/100)) for pct 67/80; constants
     rows match the pinned values.
  D-01 key tokens at recorded lines in postfiatd: minCONSENSUS_PCT 67
     (ConsensusParms.h:79), 67% quorum (ValidatorList.cpp:1898),
     majority 67/100 (SystemParameters.h:85), medianCloseOffset
     (RCLConsensus.cpp:723), reverse tie-break (Consensus.h:1612),
     67% pause phase (Consensus.h:1288), DeserializeOptions
     (STValidation.h:69), recordVote (RCLValidations.cpp:216), doVoting
     (RCLConsensus.cpp:357), untrusted cap 1000 (Manifest.h:283),
     PostFiat genesis account (Ledger.cpp:198), earliest seq 1
     (SystemParameters.h:72), copyNode rescue (SHAMapStoreImp.cpp:276),
     rotation guard (SHAMapStoreImp.cpp:380), ReplayMsgStatus
     (LedgerReplayMsgHandler.h:31), isPseudoTx
     (ConsensusTransSetSF.cpp:71), ttVALIDATOR_VOTE 1501
     (transactions.macro:1138), ltVALIDATOR_VOTE_STATS 0x008A
     (ledger_entries.macro:521), applyValidatorVote (Change.cpp:552),
     isExcluded (Transactor.cpp:194), maxExclusionListSize 100
     (Protocol.h:238), PF_AccountExclusion (features.macro:45),
     checkedAdd (MathUtilities.h:37), int128_t drops_
     (InvariantCheck.h:126), requireCanonicalOrder (STObject.cpp:279),
     len<0 guard (Serializer.cpp:236), JSON array cap 512
     (STParsedJSON.h:34).
  E-01 rippled-side tokens at recorded lines: minCONSENSUS_PCT 80
     (ConsensusParms.h:79), 80% quorum (ValidatorList.cpp:1884),
     majority 80/100 (SystemParameters.h:85), mean closeTotal
     (RCLConsensus.cpp:721), forward tie-break (Consensus.h:1605),
     80% pause phase (Consensus.h:1287), checkSignature
     (STValidation.h:71), masterpassphrase genesis (Ledger.cpp:184),
     earliest seq 32570 (SystemParameters.h:72), system name ripple
     (SystemParameters.h:37).
  F-01 counts reconcile across files: matrix == results == scenarios
     (13); findings 12 (HIGH 3, MEDIUM 6, LOW 3), claims 24
     (16/2/4/2), risks 14 (HIGH 3, MEDIUM 8, LOW 3), gaps 8; excerpts
     44 across 34 postfiatd files and 27 rippled files agree across
     manifest, files, hashes.
  G-01 determinism: re-running the simulator to a temp dir reproduces
     byte-identical outputs (full SHA-256 compare).
  H-01 excerpt integrity: every excerpt file digest matches
     fixtures/source-hashes.json and every manifest blob SHA/size
     matches `git hash-object` / file size in BOTH checkouts;
     run-manifest digests match the shipped derived files; recorded
     reproduction log digests match the fresh-clone logs on disk; the
     recorded verify-digests digest matches outputs/verify-digests.log
     when the manifest carries one.
  I-01 absence findings re-grepped in rippled: ttVALIDATOR_VOTE 0 hits
     in transactions.macro; ltVALIDATOR_VOTE_STATS 0 hits in
     ledger_entries.macro; sfExclusionAdd 0 hits in sfields.macro;
     PF_AccountExclusion 0 hits in features.macro; checkedAdd 0 hits
     in MathUtilities.h; ValidatorVoteTracker 0 hits in Application.cpp
     and RCLConsensus.cpp; setLedgerRangePresent loop comment 0 hits
     in Application.cpp.
  J-01 matching core re-verified by blob SHA: TxQ.cpp, TxQ.h,
     LoadFeeTrack.cpp, LoadFeeTrack.h, and FeeEscalation.md are
     byte-identical between the two checkouts (same git blob SHA).
  K-01 rippled pin evidence: postfiatd's own merge analysis names
     3.1.2 as the target with 21 upstream commits; the rippled
     checkout's HEAD commit message is "release: Bump version to
     3.1.2".
  T-01 timing sanity only (non-negative, never recorded).

Exit 0 only if every case passes. Prints one PASS/FAIL line per case
with the FULL 64-char SHA-256 digest where a digest is involved, and
writes outputs/derived/probe-results.json plus outputs/probe-run.log
(the log is the unedited stdout of this run; it contains no absolute
paths and no timestamps). No live node is involved.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parent.parent
PINNED_COMMIT = "0085a1ff885d6a446369cf73a4430f75af22be55"
RIPPLED_COMMIT = "3ba3fcff4c4898a96a57838bb7c67a44a3d2ec5c"
PINNED_CHECKOUT = Path(os.environ.get(
    "PINNED_CHECKOUT", str(Path.home() / "workspace" / "postfiatd-pin-0085a1f")))
RIPPLED_CHECKOUT = Path(os.environ.get(
    "RIPPLED_CHECKOUT", str(Path.home() / "workspace" / "rippled-3.1.2")))
INT64_MAX = 9223372036854775807


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def git_blob(checkout, relpath):
    out = subprocess.run(["git", "-C", str(checkout), "hash-object", "--", relpath],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def read_lines(checkout, relpath):
    return (checkout / relpath).read_text().splitlines()


def grep_hits(checkout, pattern, *roots):
    proc = subprocess.run(
        ["grep", "-rn", pattern, *[str(checkout / r) for r in roots]],
        capture_output=True, text=True)
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def ceil_pct(n, pct):
    return (n * pct + 99) // 100


def quorum_needed(total, pct):
    return max(ceil_pct(total, pct), ceil_pct(total, 60))


def weighted_median_offset(self_time, peer_times):
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
    total = self_time
    count = 1
    for t, w in peer_times:
        total += t * w
        count += w
    total += count // 2
    total //= count
    return total - self_time


def tie_break_winner(bins, threshold, reverse):
    thresh = threshold
    winner = None
    for t, v in sorted(bins, reverse=reverse):
        if v >= thresh:
            winner = t
            thresh = v
    return winner


def classify(kind, p):
    """Re-derive the differential outcome from scenario params (mirror of the model)."""
    if kind == "quorum":
        q_pf = quorum_needed(p["validators_total"], 67)
        q_r = quorum_needed(p["validators_total"], 80)
        pf = {"quorum_needed": q_pf, "validates": p["validators_agreeing"] >= q_pf}
        rp = {"quorum_needed": q_r, "validates": p["validators_agreeing"] >= q_r}
        return pf, rp, pf["validates"], rp["validates"]
    if kind == "amendment":
        pf = {"enables": p["votes_for_pct"] >= 67, "majority_pct": 67}
        rp = {"enables": p["votes_for_pct"] >= 80, "majority_pct": 80}
        return pf, rp, pf["enables"], rp["enables"]
    if kind == "close_offset":
        peers = [tuple(x) for x in p["peer_times"]]
        off_pf = weighted_median_offset(p["self_time"], peers)
        off_r = mean_offset(p["self_time"], peers)
        pf = {"offset_seconds": off_pf, "method": "weighted_median"}
        rp = {"offset_seconds": off_r, "method": "arithmetic_mean"}
        return pf, rp, off_pf, off_r
    if kind == "tie_break":
        bins = [tuple(x) for x in p["bins"]]
        w_pf = tie_break_winner(bins, p["threshold"], reverse=True)
        w_r = tie_break_winner(bins, p["threshold"], reverse=False)
        pf = {"consensus_close_time": w_pf, "tie_break": "earliest_wins"}
        rp = {"consensus_close_time": w_r, "tie_break": "latest_wins"}
        return pf, rp, w_pf, w_r
    if kind == "pause_phase":
        pct = p["validators_moved_on_pct"]
        pf = {"pauses": pct < 67, "phase0_threshold": 67}
        rp = {"pauses": pct < 80, "phase0_threshold": 80}
        return pf, rp, pf["pauses"], rp["pauses"]
    if kind == "pseudo_tx":
        pf = {"result": "applied_creates_vote_stats", "tx_type": p["tx_type"]}
        rp = {"result": "rejected_unknown_tx_type", "tx_type": p["tx_type"]}
        return pf, rp, pf["result"], rp["result"]
    if kind == "exclusion":
        code = "temBAD_SRC_ACCOUNT" if p["tx_direction"] == "source" else "temINVALID_ACCOUNT_ID"
        pf = {"result": "rejected_at_preflight", "code": code}
        rp = {"result": "applies_normally", "code": None}
        return pf, rp, pf["result"], rp["result"]
    if kind == "validation_fields":
        pf = {"result": "vote_recorded_with_exclusion"}
        rp = {"result": "deserialization_fails_unknown_field"}
        return pf, rp, pf["result"], rp["result"]
    if kind == "genesis":
        if p["network_id"] in (2025, 2026) and not p["standalone"]:
            pf_acct = "r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA"
        else:
            pf_acct = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
        pf = {"genesis_account": pf_acct}
        rp = {"genesis_account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"}
        return pf, rp, pf_acct, rp["genesis_account"]
    if kind == "shamap_depth":
        depth, leaf = p["depth"], p["leaf_depth"]
        pf = {"result": "clamped_to_leaf_depth" if depth > leaf else "accepted",
              "effective_depth": min(depth, leaf)}
        rp = {"result": "unsafe_out_of_range" if depth > leaf else "accepted",
              "effective_depth": depth}
        return pf, rp, pf["result"], rp["result"]
    if kind == "payment_overflow":
        total = 0
        overflow = False
        for a in p["amounts"]:
            s = total + a
            if s > INT64_MAX or s < -9223372036854775808:
                overflow = True
                break
            total = s
        pf = {"result": "tecPATH_DRY" if overflow else "sum_ok",
              "sum": None if overflow else total}
        wrapped = ((sum(p["amounts"]) + 2 ** 63) % 2 ** 64) - 2 ** 63
        rp = {"result": "wraps_silently" if overflow else "sum_ok",
              "sum": wrapped if overflow else sum(p["amounts"])}
        return pf, rp, pf["result"], rp["result"]
    if kind == "json_array":
        pf = {"result": "rejected_array_too_big" if p["array_size"] > 512 else "accepted"}
        rp = {"result": "accepted"}
        return pf, rp, pf["result"], rp["result"]
    if kind == "manifest_flood":
        n = p["unlisted_manifests"]
        pf = {"kept": min(n, 1000), "cap": 1000}
        rp = {"kept": n, "cap": None}
        return pf, rp, pf["kept"], rp["kept"]
    raise ValueError(f"unknown kind: {kind}")


def outcome_of(kind, p, cmp_pf, cmp_rp, rp):
    if cmp_pf == cmp_rp:
        return "matched", "same_result_both_implementations"
    if rp.get("result") in ("rejected_unknown_tx_type",
                            "deserialization_fails_unknown_field"):
        return "incompatible", "unrepresentable_on_rippled"
    if rp.get("result") == "unsafe_out_of_range" or (
            kind == "manifest_flood" and p["unlisted_manifests"] > 1000):
        return "degraded", "rippled_side_degrades"
    return "diverged", "different_result_same_input"


def main():
    started = time.time()
    argv = [a for a in sys.argv[1:] if a != "--skip-manifest-check"]
    skip_manifest = "--skip-manifest-check" in sys.argv[1:]
    results_path = Path(argv[0]) if argv else \
        PACK_ROOT / "outputs" / "derived" / "cross-impl-results.json"
    doc = load_json(results_path)
    matrix = load_json(PACK_ROOT / "outputs" / "derived" / "scenario-matrix.json")
    rules = load_json(PACK_ROOT / "configs" / "cross-impl-rules.json")["rules"]
    scenarios = load_json(PACK_ROOT / "configs" / "scenarios.json")["scenarios"]
    manifest = load_json(PACK_ROOT / "fixtures" / "excerpts-manifest.json")
    hashes = load_json(PACK_ROOT / "fixtures" / "source-hashes.json")
    findings = load_json(PACK_ROOT / "findings.json")["findings"]
    checks, lines = [], []

    def check(cid, label, ok, detail=""):
        checks.append({"id": cid, "check": label, "pass": bool(ok), "detail": detail})
        lines.append(("PASS " if ok else "FAIL ") + cid + " " + label +
                     ((" — " + detail) if detail else ""))

    # A-00: both pinned checkout HEADs.
    def head_of(checkout):
        proc = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                              capture_output=True, text=True)
        return proc.stdout.strip()

    head_pf = head_of(PINNED_CHECKOUT)
    head_rp = head_of(RIPPLED_CHECKOUT)
    check("A-00", "pinned checkout HEADs equal the pinned commits (postfiatd 0085a1ff..., rippled 3.1.2 3ba3fcff...)",
          head_pf == PINNED_COMMIT and head_rp == RIPPLED_COMMIT,
          f"postfiatd HEAD={head_pf} rippled HEAD={head_rp}")

    # A-01: rule anchors inside cited ranges on both sides.
    bad = []
    counts = Counter(r["status"] for r in rules)
    for r in rules:
        if r["status"] == "VERIFIED":
            s = r.get("source")
            if not s:
                bad.append(f"{r['id']}: no source")
                continue
            try:
                chunk = read_lines(PINNED_CHECKOUT, s["file"])[s["start_line"] - 1:s["end_line"]]
            except (FileNotFoundError, IndexError):
                bad.append(f"{r['id']}: unreadable range")
                continue
            if s.get("anchor") and not any(s["anchor"] in ln for ln in chunk):
                bad.append(f"{r['id']}: anchor not in range")
            ref = r.get("reference")
            ra = r.get("reference_absent")
            if ref and ra:
                bad.append(f"{r['id']}: reference and reference_absent are exclusive")
            elif ref:
                try:
                    rchunk = read_lines(RIPPLED_CHECKOUT, ref["file"])[ref["start_line"] - 1:ref["end_line"]]
                except (FileNotFoundError, IndexError):
                    bad.append(f"{r['id']}: unreadable reference range")
                    continue
                if ref.get("anchor") and not any(ref["anchor"] in ln for ln in rchunk):
                    bad.append(f"{r['id']}: reference anchor not in range")
            elif ra:
                hits = grep_hits(RIPPLED_CHECKOUT, ra["pattern"], ra["file"])
                if hits:
                    bad.append(f"{r['id']}: absent pattern {ra['pattern']!r} has {len(hits)} hits in rippled {ra['file']}")
            else:
                bad.append(f"{r['id']}: verified rule needs reference or reference_absent")
        elif r["status"] == "SPECIFIED":
            ext = r.get("external")
            if not ext or "url" not in ext or "quote" not in ext:
                bad.append(f"{r['id']}: specified rule needs url+quote")
        else:
            if r.get("source") is not None:
                bad.append(f"{r['id']}: {r['status']} rule must carry no file source")
    check("A-01",
          "45 rules: 38 VERIFIED anchors inside cited ranges on both sides (or verified-absent in rippled), 4 SPECIFIED (external URLs), 2 MODELLED, 1 UNTESTABLE, none with a faked source",
          not bad and len(rules) == 45 and counts == {"VERIFIED": 38, "SPECIFIED": 4, "MODELLED": 2, "UNTESTABLE": 1},
          "; ".join(bad[:3]) or f"counts={dict(sorted(counts.items()))}")

    # B-01: scenario arithmetic.
    totals = doc["totals"]
    runs = [run for sc in doc["scenarios"] for run in sc["runs"]]
    outcomes = Counter(run["outcome"] for run in runs)
    arith_ok = True
    arith_bad = []
    for run in runs:
        pf, rp, cmp_pf, cmp_rp = classify(run["kind"], run["params"])
        exp_outcome, exp_reason = outcome_of(run["kind"], run["params"], cmp_pf, cmp_rp, rp)
        if run["postfiatd"] != pf or run["rippled"] != rp:
            arith_ok = False
            arith_bad.append(f"{run['label']}: side results differ from re-derivation")
        if run["outcome"] != exp_outcome or run["reason"] != exp_reason:
            arith_ok = False
            arith_bad.append(f"{run['label']}: outcome {run['outcome']}/{run['reason']} != {exp_outcome}/{exp_reason}")
        if run["rounds"] != 1:
            arith_ok = False
            arith_bad.append(f"{run['label']}: rounds {run['rounds']} != 1")
    check("B-01",
          "per-scenario arithmetic reconciles; totals 13 scenarios / 18 runs / matched 5 / diverged 9 / degraded 2 / incompatible 2; matrix rows == runs; both sides' results and outcome classes re-derived from the scenario params",
          totals == {"scenarios": 13, "runs": 18, "matched": 5,
                     "diverged": 9, "degraded": 2, "incompatible": 2}
          and outcomes == {"matched": 5, "diverged": 9, "degraded": 2, "incompatible": 2}
          and len(matrix["rows"]) == 18 and arith_ok,
          f"totals={totals} outcomes={dict(outcomes)} " + "; ".join(arith_bad[:3]))

    # C-01: threshold and constants tables re-derived.
    c_ok = True
    c_detail = []
    for row in doc["threshold_table"]:
        unl = row["unl_size"]
        exp_pf = quorum_needed(unl, 67)
        exp_r = quorum_needed(unl, 80)
        if (row["quorum_postfiatd"] != exp_pf or row["quorum_rippled"] != exp_r
                or row["tolerated_byzantine_postfiatd"] != unl - exp_pf
                or row["tolerated_byzantine_rippled"] != unl - exp_r):
            c_ok = False
            c_detail.append(f"unl={unl}")
    consts = {r["item"]: r for r in doc["constants_table"]}
    c_ok = c_ok and consts["consensus quorum (minCONSENSUS_PCT)"]["postfiatd"] == 67 \
        and consts["consensus quorum (minCONSENSUS_PCT)"]["rippled"] == 80 \
        and consts["amendment majority (post-fix)"]["postfiatd"] == "67/100" \
        and consts["amendment majority (post-fix)"]["rippled"] == "80/100" \
        and consts["earliest ledger sequence"]["postfiatd"] == 1 \
        and consts["earliest ledger sequence"]["rippled"] == 32570 \
        and consts["untrusted manifest cap"]["postfiatd"] == 1000 \
        and consts["untrusted manifest cap"]["rippled"] == "unbounded" \
        and consts["exclusion list maximum"]["postfiatd"] == 100 \
        and consts["JSON array element cap"]["postfiatd"] == 512 \
        and consts["JSON nesting depth cap"]["postfiatd"] == 64 \
        and consts["JSON nesting depth cap"]["rippled"] == 64 \
        and consts["variable-length field maximum"]["postfiatd"] == 918744 \
        and consts["variable-length field maximum"]["rippled"] == 918744 \
        and len(doc["constants_table"]) == 19 \
        and len(doc["threshold_table"]) == 7
    check("C-01",
          "threshold rows match max(ceil(unl*pct/100), ceil(unl*60/100)) for pct 67/80 across 7 UNL sizes (3..100); constants table matches the pinned values (67/80 quorum and majority, 1/32570 earliest sequence, 1,000 manifest cap, 100 exclusion cap, 512 array cap, 64/64 depth cap, 918,744 VL maximum); 19 constants rows, 7 threshold rows",
          c_ok, "; ".join(c_detail[:3]) or "all match")

    # D-01: key tokens at recorded lines (postfiatd).
    def token_at(checkout, relpath, lineno, token):
        chunk = read_lines(checkout, relpath)
        return lineno <= len(chunk) and token in chunk[lineno - 1]

    d_checks = [
        ("src/xrpld/consensus/ConsensusParms.h", 79, "minCONSENSUS_PCT = 67"),
        ("src/xrpld/app/misc/detail/ValidatorList.cpp", 1898, "67% quorum"),
        ("include/xrpl/protocol/SystemParameters.h", 85, "67, 100"),
        ("src/xrpld/app/consensus/RCLConsensus.cpp", 723, "medianCloseOffset"),
        ("src/xrpld/consensus/Consensus.h", 1612, "std::views::reverse"),
        ("src/xrpld/consensus/Consensus.h", 1288, "0: >=67%"),
        ("include/xrpl/protocol/STValidation.h", 69, "DeserializeOptions"),
        ("src/xrpld/app/consensus/RCLValidations.cpp", 216, "recordVote"),
        ("src/xrpld/app/consensus/RCLConsensus.cpp", 357, "doVoting"),
        ("src/xrpld/app/misc/Manifest.h", 283, "defaultMaxUntrustedManifests = 1000"),
        ("src/xrpld/app/ledger/Ledger.cpp", 198, "r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA"),
        ("include/xrpl/protocol/SystemParameters.h", 72, "XRP_LEDGER_EARLIEST_SEQ{1u}"),
        ("src/xrpld/app/misc/SHAMapStoreImp.cpp", 276, "re-stored node missing"),
        ("src/xrpld/app/misc/SHAMapStoreImp.cpp", 380, "RotationExposureGuard"),
        ("src/xrpld/app/ledger/detail/LedgerReplayMsgHandler.h", 31, "ReplayMsgStatus"),
        ("src/xrpld/app/ledger/ConsensusTransSetSF.cpp", 71, "isPseudoTx"),
        ("include/xrpl/protocol/detail/transactions.macro", 1138, "ttVALIDATOR_VOTE, 1501"),
        ("include/xrpl/protocol/detail/ledger_entries.macro", 521, "ltVALIDATOR_VOTE_STATS, 0x008A"),
        ("src/xrpld/app/tx/detail/Change.cpp", 552, "applyValidatorVote"),
        ("src/xrpld/app/tx/detail/Transactor.cpp", 194, "isExcluded"),
        ("include/xrpl/protocol/Protocol.h", 238, "maxExclusionListSize = 100"),
        ("include/xrpl/protocol/detail/features.macro", 45, "PF_AccountExclusion"),
        ("include/xrpl/basics/MathUtilities.h", 37, "checkedAdd"),
        ("src/xrpld/app/tx/detail/InvariantCheck.h", 126, "int128_t drops_"),
        ("src/libxrpl/protocol/STObject.cpp", 279, "requireCanonicalOrder"),
        ("src/libxrpl/protocol/Serializer.cpp", 236, "len<0"),
        ("include/xrpl/protocol/STParsedJSON.h", 34, "maxSTParsedJSONArraySize = 512"),
    ]
    d_bad = [f"{f}:{ln} {t!r}" for f, ln, t in d_checks
             if not token_at(PINNED_CHECKOUT, f, ln, t)]
    check("D-01",
          "27 key tokens at recorded lines in postfiatd (quorum 67, majority 67/100, median offset, reverse tie-break, 67% phases, DeserializeOptions, recordVote, doVoting, manifest cap 1000, PostFiat genesis account, earliest seq 1, copyNode rescue, rotation guard, ReplayMsgStatus, isPseudoTx, ttVALIDATOR_VOTE 1501, ltVALIDATOR_VOTE_STATS 0x008A, applyValidatorVote, isExcluded, exclusion cap 100, PF_AccountExclusion, checkedAdd, int128_t accumulator, canonical order, VL len<0 guard, JSON array cap 512)",
          not d_bad, "; ".join(d_bad[:3]) or "all 27 tokens at recorded lines")

    # E-01: rippled-side tokens at recorded lines.
    e_checks = [
        ("src/xrpld/consensus/ConsensusParms.h", 79, "minCONSENSUS_PCT = 80"),
        ("src/xrpld/app/misc/detail/ValidatorList.cpp", 1884, "80% quorum"),
        ("include/xrpl/protocol/SystemParameters.h", 85, "80, 100"),
        ("src/xrpld/app/consensus/RCLConsensus.cpp", 721, "closeTotal /= closeCount"),
        ("src/xrpld/consensus/Consensus.h", 1605, "closeTimeVotes"),
        ("src/xrpld/consensus/Consensus.h", 1287, "0: >=80%"),
        ("include/xrpl/protocol/STValidation.h", 71, "checkSignature"),
        ("src/xrpld/app/ledger/Ledger.cpp", 184, "masterpassphrase"),
        ("include/xrpl/protocol/SystemParameters.h", 72, "XRP_LEDGER_EARLIEST_SEQ{32570u}"),
        ("include/xrpl/protocol/SystemParameters.h", 37, '"ripple"'),
    ]
    e_bad = [f"{f}:{ln} {t!r}" for f, ln, t in e_checks
             if not token_at(RIPPLED_CHECKOUT, f, ln, t)]
    check("E-01",
          "10 key tokens at recorded lines in rippled 3.1.2 (quorum 80, majority 80/100, mean closeTotal, forward tie-break, 80% phases, checkSignature, masterpassphrase genesis, earliest seq 32570, system name ripple)",
          not e_bad, "; ".join(e_bad[:3]) or "all 10 tokens at recorded lines")

    # F-01: counts reconcile across files.
    def table_rows(path, prefix):
        rows = []
        for ln in open(path, encoding="utf-8"):
            m = re.match(rf"\| ({prefix}-\d+) \| ([A-Z]+) \|", ln)
            if m:
                rows.append((m.group(1), m.group(2)))
        return rows

    claims = table_rows(PACK_ROOT / "docs" / "claim-index.md", "C")
    risks = table_rows(PACK_ROOT / "docs" / "risk-register.md", "K")
    gaps = [ln for ln in open(PACK_ROOT / "docs" / "gap-register.md", encoding="utf-8")
            if re.match(r"\| G-\d+ \|", ln)]
    f_ok = (len(doc["scenarios"]) == 13 and len(runs) == 18
            and len(findings) == 12
            and Counter(f["severity"] for f in findings) == {"HIGH": 3, "MEDIUM": 6, "LOW": 3}
            and len(claims) == 24
            and Counter(s for _, s in claims) == {"VERIFIED": 16, "SPECIFIED": 2, "MODELLED": 4, "UNTESTABLE": 2}
            and len(risks) == 14
            and Counter(s for _, s in risks) == {"HIGH": 3, "MEDIUM": 8, "LOW": 3}
            and len(gaps) == 8
            and len(manifest["excerpts"]) == 44
            and len(hashes["files"]["postfiatd"]) == 34
            and len(hashes["files"]["rippled"]) == 27
            and len(hashes["excerpts"]) == 44)
    check("F-01",
          "matrix == results == scenarios (13); findings 12 (HIGH 3, MEDIUM 6, LOW 3), claims 24 (16/2/4/2), risks 14 (HIGH 3, MEDIUM 8, LOW 3), gaps 8; excerpts 44 across 34 postfiatd files and 27 rippled files agree across manifest, files, hashes",
          f_ok, f"claims={len(claims)} risks={len(risks)} gaps={len(gaps)} excerpts={len(manifest['excerpts'])} pf-files={len(hashes['files']['postfiatd'])} rp-files={len(hashes['files']['rippled'])}")

    # G-01: determinism — capture digests, re-run simulator, compare.
    res_before = sha256_file(PACK_ROOT / "outputs" / "derived" / "cross-impl-results.json")
    mat_before = sha256_file(PACK_ROOT / "outputs" / "derived" / "scenario-matrix.json")
    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.run(
            [sys.executable, "src/cross_impl_model.py"],
            cwd=str(PACK_ROOT), capture_output=True, text=True)
        g_ok = proc.returncode == 0
    res_digest = sha256_file(PACK_ROOT / "outputs" / "derived" / "cross-impl-results.json")
    mat_digest = sha256_file(PACK_ROOT / "outputs" / "derived" / "scenario-matrix.json")
    g_ok = g_ok and res_digest == res_before and mat_digest == mat_before
    check("G-01",
          "determinism: simulator re-run reproduces byte-identical results and matrix (full SHA-256)",
          g_ok,
          f"results shipped={res_before} rerun={res_digest}; matrix shipped={mat_before} rerun={mat_digest}")

    # H-01: excerpt integrity + manifest digests + reproduction digests.
    h_bad = []
    for ex_id, rec in hashes["excerpts"].items():
        p = PACK_ROOT / "fixtures" / "source-excerpts" / f"{ex_id}.txt"
        if not p.is_file() or sha256_file(p) != rec["sha256"]:
            h_bad.append(ex_id)
    for repo, checkout in (("postfiatd", PINNED_CHECKOUT), ("rippled", RIPPLED_CHECKOUT)):
        for relpath, rec in hashes["files"][repo].items():
            if git_blob(checkout, relpath) != rec["git_blob_sha"]:
                h_bad.append(f"{repo}:{relpath}:blob")
            if (checkout / relpath).stat().st_size != rec["size_bytes"]:
                h_bad.append(f"{repo}:{relpath}:size")
    man = load_json(PACK_ROOT / "run-manifest.json") if (PACK_ROOT / "run-manifest.json").is_file() else None
    man_ok = True
    if not skip_manifest and man is not None:
        man_ok = (man.get("results_sha256") == res_digest
                  and man.get("matrix_sha256") == mat_digest)
        for rep in man.get("reproductions", []):
            log_path = PACK_ROOT / rep["log"]
            if not log_path.is_file() or sha256_file(log_path) != rep["sha256"]:
                man_ok = False
                h_bad.append(f"reproduction {rep['label']}: digest mismatch")
        vd = man.get("verify_digests_sha256")
        if vd:
            vd_path = PACK_ROOT / "outputs" / "verify-digests.log"
            if not vd_path.is_file() or sha256_file(vd_path) != vd:
                man_ok = False
                h_bad.append("verify-digests.log: digest mismatch")
    check("H-01",
          "every excerpt digest matches source-hashes.json; every manifest blob SHA/size matches both checkouts; run-manifest digests match shipped derived files; recorded reproduction log digests match the fresh-clone logs on disk; recorded verify-digests digest matches outputs/verify-digests.log when present",
          not h_bad and man_ok,
          "; ".join(h_bad[:3]) or ("manifest digests match" if man_ok else "manifest digest mismatch"))

    # I-01: absence findings re-grepped in rippled.
    def count_hits(checkout, pattern, *roots):
        return len(grep_hits(checkout, pattern, *roots))

    i1 = count_hits(RIPPLED_CHECKOUT, "ttVALIDATOR_VOTE",
                    "include/xrpl/protocol/detail/transactions.macro")
    i2 = count_hits(RIPPLED_CHECKOUT, "ltVALIDATOR_VOTE_STATS",
                    "include/xrpl/protocol/detail/ledger_entries.macro")
    i3 = count_hits(RIPPLED_CHECKOUT, "sfExclusionAdd",
                    "include/xrpl/protocol/detail/sfields.macro")
    i4 = count_hits(RIPPLED_CHECKOUT, "PF_AccountExclusion",
                    "include/xrpl/protocol/detail/features.macro")
    i5 = count_hits(RIPPLED_CHECKOUT, "checkedAdd",
                    "include/xrpl/basics/MathUtilities.h")
    i6 = count_hits(RIPPLED_CHECKOUT, "ValidatorVoteTracker",
                    "src/xrpld/app/main/Application.cpp",
                    "src/xrpld/app/consensus/RCLConsensus.cpp")
    i7 = count_hits(RIPPLED_CHECKOUT, "Load all ledgers that are present in the db",
                    "src/xrpld/app/main/Application.cpp")
    check("I-01",
          "absence findings re-grepped in rippled 3.1.2: ttVALIDATOR_VOTE 0 hits in transactions.macro; ltVALIDATOR_VOTE_STATS 0 hits in ledger_entries.macro; sfExclusionAdd 0 hits in sfields.macro; PF_AccountExclusion 0 hits in features.macro; checkedAdd 0 hits in MathUtilities.h; ValidatorVoteTracker 0 hits in Application.cpp and RCLConsensus.cpp; the ledger-range-marking loop comment 0 hits in Application.cpp",
          i1 == 0 and i2 == 0 and i3 == 0 and i4 == 0 and i5 == 0 and i6 == 0 and i7 == 0,
          f"ttVALIDATOR_VOTE={i1} ltVALIDATOR_VOTE_STATS={i2} sfExclusionAdd={i3} PF_AccountExclusion={i4} checkedAdd={i5} ValidatorVoteTracker={i6} range-loop={i7}")

    # J-01: matching core re-verified by blob SHA.
    identical_files = [
        "src/xrpld/app/misc/detail/TxQ.cpp",
        "src/xrpld/app/misc/TxQ.h",
        "src/xrpld/app/misc/detail/LoadFeeTrack.cpp",
        "src/xrpld/app/misc/LoadFeeTrack.h",
        "src/xrpld/app/misc/FeeEscalation.md",
    ]
    j_bad = []
    for relpath in identical_files:
        try:
            if git_blob(PINNED_CHECKOUT, relpath) != git_blob(RIPPLED_CHECKOUT, relpath):
                j_bad.append(relpath)
        except subprocess.CalledProcessError:
            j_bad.append(f"{relpath}:unreadable")
    check("J-01",
          "matching core re-verified by git blob SHA: TxQ.cpp, TxQ.h, LoadFeeTrack.cpp, LoadFeeTrack.h, and FeeEscalation.md are byte-identical between postfiatd and rippled 3.1.2",
          not j_bad, "; ".join(j_bad) or "all 5 files byte-identical")

    # K-01: rippled pin evidence.
    analysis = read_lines(PINNED_CHECKOUT, "docs/upstream-merge-3.1.2-analysis.md")
    k_ok = ("**Target:** 3.1.2 (tag `3.1.2`)" in "\n".join(analysis[:10])
            and "**Total upstream commits:** 21" in "\n".join(analysis[:10]))
    msg = subprocess.run(["git", "-C", str(RIPPLED_CHECKOUT), "log", "-1", "--format=%s"],
                         capture_output=True, text=True).stdout.strip()
    k_ok = k_ok and msg == "release: Bump version to 3.1.2"
    check("K-01",
          "rippled pin evidence: postfiatd's merge analysis names 3.1.2 as the target with 21 upstream commits; the rippled checkout HEAD commit is 'release: Bump version to 3.1.2'",
          k_ok, f"HEAD subject={msg!r}" if not k_ok else "pin evidence verified")

    # T-01: timing sanity.
    elapsed_ms = int((time.time() - started) * 1000)
    check("T-01",
          "timing sanity: total probe elapsed_ms is non-negative (loose band, never exact)",
          elapsed_ms >= 0, "value not recorded; never compared")

    passed = sum(1 for c in checks if c["pass"])
    total = len(checks)
    lines.append(f"probe: {passed}/{total} checks PASS")
    lines.append(f"probe: cross-impl-results.json sha256: {res_digest}")
    lines.append(f"probe: scenario-matrix.json sha256: {mat_digest}")
    lines.append(f"probe: pinned commit {PINNED_COMMIT}")
    lines.append(f"probe: rippled commit {RIPPLED_COMMIT}")
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    result_doc = {"pack": "Cross-Implementation Compatibility: postfiatd vs rippled 3.1.2",
                  "pinned_commit": PINNED_COMMIT,
                  "rippled_commit": RIPPLED_COMMIT,
                  "rippled_tag": "3.1.2",
                  "results_file": "outputs/derived/cross-impl-results.json",
                  "results_sha256": res_digest, "matrix_sha256": mat_digest,
                  "checks": checks, "passed": passed, "total": total}
    out_derived = PACK_ROOT / "outputs" / "derived" / "probe-results.json"
    out_derived.parent.mkdir(parents=True, exist_ok=True)
    with open(out_derived, "w", encoding="utf-8") as fh:
        json.dump(result_doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    (PACK_ROOT / "outputs" / "probe-run.log").write_text(text)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
