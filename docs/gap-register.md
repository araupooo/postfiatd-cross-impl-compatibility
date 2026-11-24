# Gap register

Things this pack does not establish, because the pinned sources alone
cannot decide them. Every gap is source-only: it names what is missing
from the code or the evidence, not what a live deployment might show.

| Gap | Gap | Why it is a gap |
| --- | --- | --- |
| G-01 | No mixed network was run: whether postfiatd and rippled nodes reach consensus together is untested. | Running both implementations together needs live nodes; the pack compares code and models the consequences (claim C-23, rule R-30). |
| G-02 | No measurement of doVoting per-ledger cost: vote tracking runs every ledger, but its CPU and I/O cost is unmeasured. | The code path exists (RCLConsensus.cpp:353-361, E12) but no benchmark was run; the pack cannot say how much it costs under load (risk K-14). |
| G-03 | No live test of exclusion propagation timing: the design applies one exclusion change per 10 ledgers, but the timing was not observed. | The cadence is documented in docs/Exclusions.md (R-29); no run demonstrates it. |
| G-04 | Cross-chain bridge behavior is out of scope: the XChain witness server and bridge attestation code were not compared. | The pack covers consensus, ledger application, and transaction processing only; bridge code is a separate surface. |
| G-05 | The exact fork commit is indistinguishable within the 5-commit plateau (2026-03-11–12): the plateau commits differ only in BuildInfo.cpp version strings, which postfiatd overwrote. | Pin method (`docs/methodology.md`): blob-SHA tree comparison plus the in-tree merge analysis bounds the base to 3.1.2; the exact commit cannot be proven (risk K-13). |
| G-06 | Amendment majority boundary semantics (>= vs >) are not exercised at exactly 67% or 80%: the scenarios use 70% and 85%. | The model applies the threshold as at-least; the boundary case is a one-vote difference the pack does not simulate. |
| G-07 | No live close-time measurement under real clock skew: the median/mean divergence is modelled on static inputs, not observed on a running network. | The model computes both offsets from the same inputs (scenario S-03); a live run would need skewed validator clocks (claim C-24). |
| G-08 | The manifest flood threshold (1,000) was not tested against a live peer flood: the cap is code-verified, not load-tested. | The cap and eviction logic exist in code (Manifest.h:246-290, E13); the flood behavior is modelled (scenario S-13). |
