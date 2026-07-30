---
name: consistency-antagonism-review
description: 'Review code for inconsistencies, contract mismatches, and antagonistic functions that should behave as opposites but drift apart. Use when reviewing implementations, hunting regressions, or checking paired APIs like add/remove, enable/disable, encode/decode, start/stop, and input/output transformations.'
argument-hint: 'What codebase or slice should be reviewed?'
---

# Consistency and Antagonism Review

## What This Skill Does
Use this skill to inspect code for:
- inconsistent behavior between related functions, modules, or layers
- functions that should be opposite or inverse but produce the wrong result
- naming and contract drift between an API and its implementation
- asymmetric validation, error handling, or state updates
- duplicated logic that diverges in subtle ways

An antagonistic function pair is any pair that should move state in opposite directions or transform data in reverse directions, such as add/remove, enable/disable, encode/decode, import/export, lock/unlock, start/stop, open/close, increment/decrement, and normalize/denormalize.

## When to Use
Use this skill when you need to:
- review code for subtle logic regressions
- compare paired endpoints, helpers, or reducers for symmetry
- check whether a change broke the inverse of an existing operation
- find places where the code says one thing but does another
- validate that opposite flows handle the same edge cases in mirrored ways

## Review Procedure
1. Identify the narrow scope being reviewed and the main data or state being transformed.
2. List the obvious paired or mirrored functions, handlers, endpoints, or branches in that scope.
3. Compare their contracts first: inputs, outputs, side effects, invariants, and error paths.
4. Trace the implementation of each pair and check whether the direction of change is actually opposite where expected.
5. Look for asymmetry in:
   - state mutation
   - default values
   - null or empty handling
   - permission checks
   - persistence or caching
   - return shape and status codes
6. Verify naming against behavior. If a function name implies an opposite action, confirm the implementation matches the name.
7. Check for duplicated code that was edited in only one direction.
8. If a mismatch is found, propose the smallest local fix that restores the mirrored behavior.
9. Report only concrete findings that can be tied to a specific file and line range.

## What to Flag
Flag a finding when at least one of these is true:
- one side of a pair updates state and the opposite side does not undo it
- two related functions return incompatible shapes or meanings
- one branch handles an edge case while the inverse branch ignores it
- a helper is reused in a way that flips meaning unexpectedly
- a name strongly implies an inverse operation, but the implementation is not inverse
- two code paths that should stay symmetric have diverged

## What Good Results Look Like
A useful review output should include:
- the pair or inconsistency that was checked
- why the behavior is suspicious
- the user-visible or data-level impact
- the exact file location for each issue
- the smallest fix direction, without rewriting unrelated code
- a concrete remediation suggestion that keeps the pair aligned

## Completion Checks
Before finishing, confirm that:
- each suspected pair was compared against its opposite or counterpart
- findings are grounded in observable code, not naming alone
- no obvious mirrored path was skipped in the reviewed slice
- any conclusion about symmetry is supported by implementation details
- each finding includes a practical local remediation path

## Suggested Output Format
When reporting back, prefer this structure:
- Finding: short statement of the inconsistency or antagonistic mismatch
- Evidence: file and line references for the paired code
- Impact: what breaks or becomes unreliable
- Fix direction: the smallest corrective change

## Notes
Keep the review local. Start with the closest paired functions or mirrored flow instead of scanning the whole repository.
