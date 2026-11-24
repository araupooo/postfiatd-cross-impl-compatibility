# Operator decision memo

How to run postfiatd next to rippled 3.1.2 without forking, from the
pinned code of both implementations.

## The compatibility rule in one paragraph

postfiatd is rippled 3.1.2 with a 67% consensus quorum (instead of
80%), a weighted-median close-time offset (instead of a mean), a
reversed close-time tie-break, validator vote tracking with a new
pseudo-transaction type, consensus-driven account exclusion, 36
amendment defaults flipped on, and a set of parse and arithmetic
hardening changes. The fee market, load-fee tracking, and the
disputed-transaction stall test are byte-identical. A network running
one implementation behaves like the other on most inputs — and
diverges on the inputs listed below.

## What to do

1. **Never mix implementations on one network.** A ledger with 70 of
   100 validators agreeing validates on postfiatd and not on rippled
   (scenario S-01). A ledger containing ttVALIDATOR_VOTE or
   ltVALIDATOR_VOTE_STATS is unreplayable by rippled (scenario S-06).
   An excluded account's transaction is rejected by postfiatd and
   applied by rippled (scenario S-07). Mixing implementations forks
   the network.
2. **Treat the 67% quorum as a testnet setting.** The code says so
   itself (`ValidatorList.cpp:1899-1900`: "For mainnet, this should be
   reverted to 80%"). A 67% quorum tolerates 33 Byzantine validators
   in 100 where rippled tolerates 20; keep UNL overlap high.
3. **Keep validator clocks tight.** The median and the mean agree when
   peers report the same close time and diverge when they spread: one
   peer 120 seconds off moves the rippled mean 11 seconds and the
   postfiatd median 0 seconds (scenario S-03). The median is the
   safer side under skew, but the two implementations still adjust
   differently after the same round.
4. **Stay inside the parse caps.** postfiatd rejects JSON array fields
   over 512 elements and validations that are not in canonical field
   order; rippled accepts both. Keep submitted transactions inside
   the caps and canonical order, or the two implementations disagree
   on the same submission.
5. **Audit the amendment set of a fresh network.** 36 amendments are
   on by default in postfiatd and off by default in rippled
   (features.macro). Do not assume a fresh postfiatd network behaves
   like a fresh rippled network.
6. **Watch the exclusion list size.** It caps at 100 addresses
   (`Protocol.h:238`). Rotate exclusions out when the list fills, and
   monitor the count through the exclusion_info RPC.
7. **Do not point a rippled node at a postfiatd network.** Networks
   2025/2026 start from a different genesis account
   (r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA) with earliest sequence 1;
   rippled derives rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh with earliest
   sequence 32,570. The genesis ledgers are incompatible by design.

## What is safe to assume

- Fee escalation is quadratic on both sides (byte-identical TxQ.cpp),
  load-fee tracking is identical, and the disputed-transaction stall
  test is identical logic parameterized by the quorum constant.
- The amendment majority timestamp is the parent ledger close time
  on both sides.
- The reference base is rippled 3.1.2: 1,595 of 1,702 shared files
  match by blob SHA, and the remaining 107 differ by the changes
  documented in this pack.

## Primary sources

- postfiatd `0085a1ff885d6a446369cf73a4430f75af22be55` —
  https://github.com/postfiatorg/postfiatd
- rippled 3.1.2 `3ba3fcff4c4898a96a57838bb7c67a44a3d2ec5c` —
  https://github.com/XRPLF/rippled/releases/tag/3.1.2
- XRPL consensus protocol —
  https://xrpl.org/docs/concepts/consensus-protocol
