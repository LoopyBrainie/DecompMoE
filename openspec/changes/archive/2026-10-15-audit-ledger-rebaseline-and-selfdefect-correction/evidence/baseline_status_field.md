# Baseline: the `**status**` field's existing semantics (task 1.1)

**Captured at**: `HEAD = ded0944`, working tree dirty with the 3 pre-existing
modifications (`.gitignore` / `src/decompmoe/gating.py` / `wayfinder/tickets/WF-1.md`).
None of them touches the two ledgers, so the readings below are unaffected.

## Command

```
grep -o '\*\*status\*\*：.*' .audit/gradual-review-2026-10-07/lists/direct-fixes.md | sort | uniq -c
```

## Observed output (verbatim)

```
     28 **status**：ledger 无 `status` 字段。
      1 **status**：ledger 无独立 `status` 字段；条目正文自带一条保留的 UNVERIFIABLE（被跳过的 302 条的性质未判定）。
      3 **status**：UNVERIFIABLE
```

## `opsx-changes.md` self-declaration

```
grep -n 'status.*分布' .audit/gradual-review-2026-10-07/lists/opsx-changes.md
```

```
216:- **status 分布**：8 条均无 `status` 字段（ledger 全局：NO_STATUS_FIELD 82 / UNVERIFIABLE 5 / RESOLVED_AT_HEAD 1，后 6 条均不属本桶）。
```

## Why this baseline exists

The two files above establish the fact that motivates `design.md` **D-1**:

- In `direct-fixes.md`, `**status**` is **not** an open/closed verdict. 28 of 32
  entries read "the upstream ledger carried no `status` field", 3 read
  `UNVERIFIABLE`, 1 explains that the entry body itself retains one. The field
  records **provenance about the upstream `classified.json`**, not the liveness of
  the defect.
- In `opsx-changes.md`, none of the 8 entries has the field at all, and the file
  says so itself at `:216`.

Therefore writing a new liveness verdict into the token `**status**` would make
the existing `UNVERIFIABLE` (provenance sense) and a newly written `UNVERIFIABLE`
(liveness sense) the same token pointing at two different things. D-1 keeps the
axes apart by introducing `**HEAD 复验（ded0944）**` instead.

## Reproduction

```
grep -o '\*\*status\*\*：.*' .audit/gradual-review-2026-10-07/lists/direct-fixes.md | sort | uniq -c
grep -n 'status.*分布' .audit/gradual-review-2026-10-07/lists/opsx-changes.md
```

Both must reproduce byte-for-byte for this baseline to hold.
