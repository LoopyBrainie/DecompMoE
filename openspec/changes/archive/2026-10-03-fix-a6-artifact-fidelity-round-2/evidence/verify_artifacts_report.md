== F-3: regenerated drift table ==
PASS new artifact exists
PASS archived original still present (untouched)
PASS filename matches its pin/head payload  -- file=drift_6593a06..95718cf.json payload=drift_6593a06..95718cf.json
PASS pin/head equal the archived original's  -- new=6593a06/95718cfa0b7e417935d2fbdd873eb7fec06ebb9b old=6593a06/95718cfa0b7e417935d2fbdd873eb7fec06ebb9b
PASS drift     identical key-by-key (277 keys / 570 intervals both sides)  -- new=277/570 old=277/570
PASS inserted  identical key-by-key (277 keys / 283 intervals both sides)  -- new=277/283 old=277/283
PASS modified  identical key-by-key (277 keys / 269 intervals both sides)  -- new=277/269 old=277/269
== F-2: self_check reports key-set differences ==
PASS self-check exits 0 on the real tables  -- exit=0
PASS reports interval equality with a number
PASS states the key sets are NOT identical
PASS lists the extra keys individually  -- count=12
PASS no longer prints the misleading bare 'files=' number
PASS declares key-count equality is not asserted
PASS NEGATIVE PROBE 1: an extra EMPTY key is accepted as benign  -- problems=[]
PASS   ... and is still reported in stats, not swallowed
PASS NEGATIVE PROBE 2: an extra NON-EMPTY key is REJECTED  -- problems=['drift[b]: present in MINE but not in ORIGINAL and carries NON-EMPTY intervals mine=[[7, 9]] -- this is a real disagreement, not a benign extra key']
PASS   ... and is named in stats
PASS NEGATIVE PROBE 3: a LOST key is rejected  -- problems=['drift[a]: present in ORIGINAL but MISSING in mine (original=[[1, 2]]) -- a key was lost']
PASS   ... and is named in stats
== ANNOT duplicate keys (read with ast; the module is NEVER imported) ==
PASS ANNOT literal located in the generator source
PASS ANNOT declares 19 keys (merged, none dropped)  -- count=19
PASS ANNOT has NO duplicate keys  -- dupes=[]
PASS AC-28 [边界保留] segment present in the generator source
PASS AC-28 [溯源缺口] segment present in the generator source
PASS AC-29 [分桶存疑] segment present in the generator source
PASS AC-29 [溯源缺口已消] segment present in the generator source
PASS probe copy really does contain a duplicate key
PASS guard function found in the generator
PASS guard passes on the REAL generator  -- count=19
PASS NEGATIVE PROBE: the guard RAISES on a duplicate key  -- ANNOT has 1 duplicate key(s); the earlier text is silently lost: AC-28 at L[112, 113]
PASS   ... and the message names the offending key  -- ANNOT has 1 duplicate key(s); the earlier text is silently lost: AC-28 at L[112, 113]
== generator refuses to overwrite the live list ==
PASS exits non-zero when pointed at the live list  -- exit=2
PASS says why
PASS live list still has 5 Errata sections afterwards
== lists/opsx-changes.md (read back from disk) ==
PASS 5 Errata sections  -- count=5
PASS one bare `## Errata` plus four parenthesised ones  -- heads=5
PASS exactly 1 `(A-2 ...)` Errata section(s)  -- count=1
PASS exactly 1 `(A-4 ...)` Errata section(s)  -- count=1
PASS exactly 2 `(A-6 ...)` Errata section(s)  -- count=2
PASS this change's Errata content is present
PASS 108 基线 declarations  -- count=108
PASS tally is 23 / 72 / 13 (design D1)  -- tally={'`unchanged-since-pin': 72, '`unverifiable': 13, '`touched-since-pin': 23}
PASS old 口径 passage (old figure stated as current fact) is gone from the body
PASS corrected 口径 wording states the two facts separately
PASS the old figure is still quoted somewhere, as the corrected thing
PASS restored AC-28 [边界保留] segment appears exactly once  -- count=1
== A-6 verifier: exactly one known-stale failure, no others ==
PASS A-6 verifier prints its tally  -- pMoE\openspec\changes\archive\2026-10-03-fix-a6-audit-ledger-accuracy-and-rebaseline\evidence\verify_a6_errata_report.md
PASS A-6 verifier still runs 65 checks  -- actual=65
PASS 64 of 65 A-6 checks pass (the A-6 field corrections are intact)  -- actual=64
PASS exactly ONE A-6 check fails  -- actual=1
PASS the single failure is F-errata, and nothing else  -- failures=['F-errata']
PASS F-errata's own message shows the section count is 5, not a content problem

RESULT: 52 check(s), 0 failure(s)
