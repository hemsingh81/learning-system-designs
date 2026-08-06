# 18 · Coding-Round Prep — both formats

[← Deep Dive: Python & Data](17-deepdive-python-data.md) · [Home](README.md) · [Next → Cheat Sheets](08-cheatsheets.md)

Interviews use two coding formats and I prepare for **both**: the **DSA / algorithm round** (LeetCode-style) and the **feature-building round** (build a small working thing). This page is my playbook and drill list for each — in C#, TypeScript and Python, the three languages I actually ship.

> How I frame a coding round as a 19-year architect: *"I'll think out loud, state the approach and its complexity before I type, write it clean, then test it against the edges. You'll see how I reason, not just whether I recall a trick."*

**Jump to:** [How I run any live-coding round](#how-i-run-any-live-coding-round) · [Format 1: DSA](#format-1--dsa--algorithms) · [Patterns to know cold](#the-patterns-to-know-cold) · [Complexity](#complexity-say-it-out-loud) · [Worked DSA examples](#worked-dsa-examples) · [Format 2: feature-building](#format-2--feature-building) · [Feature drill list](#feature-drill-list) · [Common mistakes](#common-mistakes-i-avoid)

---

## How I run any live-coding round

A repeatable 6-step method — it works for both formats and keeps me calm:

1. **Clarify.** Restate the problem, confirm inputs/outputs, ask about edge cases and scale. "Can the input be empty? How large? Sorted?" — this alone separates seniors from juniors.
2. **Examples.** Write one normal case and one edge case *before* coding, so I have a target.
3. **Approach + complexity.** State the plan and its Big-O out loud, and the trade-off, *before* typing. Get a nod first.
4. **Code cleanly.** Good names, small functions, no premature cleverness. Talk while I type.
5. **Test.** Run through my examples by hand, then the edges (empty, one item, duplicates, overflow).
6. **Reflect.** State the complexity, one improvement, and how I'd productionise it — my architect edge.

> The senior signal: *I clarify before I code and I test the edges after.* Juniors dive straight in; I bracket the problem.

---

## Format 1 — DSA / algorithms

The LeetCode-style round. I don't grind 500 problems — at my level I master the **patterns** and can derive the rest. Target: recognise the pattern from the problem shape, state complexity, implement cleanly.

### The patterns to know cold

| Pattern | Problem smell | Typical complexity |
|---|---|---|
| **Hash map / set** | "seen before?", counts, pairs summing to X | O(n) time, O(n) space |
| **Two pointers** | sorted array, pair/triplet, palindrome | O(n), O(1) space |
| **Sliding window** | longest/shortest substring/subarray with a condition | O(n) |
| **Binary search** | sorted, or "minimise the max" answer space | O(log n) |
| **BFS / DFS** | trees, graphs, grids, connected components | O(V+E) |
| **Heap / priority queue** | top-K, k-th largest, merge k lists | O(n log k) |
| **Dynamic programming** | "number of ways", "min/max cost", overlapping subproblems | varies |
| **Stack** | matching pairs, next-greater, expression parsing | O(n) |

If I can name the pattern, the code follows. Most interview problems are one or two of these composed.

### Complexity, said out loud

I always state time **and** space, and know the everyday costs: hash lookup O(1), sort O(n log n), nested loop O(n²), binary search O(log n). I say the trade-off explicitly — *"I'll trade O(n) space for O(n) time with a hash set here."* That verbalised trade-off is exactly the architectural thinking they want to see.

### Worked DSA examples

**Two-sum (hash map) — C#:** the canonical "seen before" pattern.
```csharp
public int[] TwoSum(int[] nums, int target) {
    var seen = new Dictionary<int, int>();          // value -> index
    for (int i = 0; i < nums.Length; i++) {
        int need = target - nums[i];
        if (seen.TryGetValue(need, out int j)) return new[] { j, i };
        seen[nums[i]] = i;                           // O(n) time, O(n) space, one pass
    }
    return Array.Empty<int>();
}
```

**Longest substring without repeats (sliding window) — TypeScript:**
```typescript
function lengthOfLongestSubstring(s: string): number {
  const lastSeen = new Map<string, number>();
  let start = 0, best = 0;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (lastSeen.has(c) && lastSeen.get(c)! >= start) start = lastSeen.get(c)! + 1; // shrink window
    lastSeen.set(c, i);
    best = Math.max(best, i - start + 1);   // O(n) time, O(k) space
  }
  return best;
}
```

**Level-order tree traversal (BFS) — Python:**
```python
from collections import deque

def level_order(root):
    if not root:
        return []
    out, q = [], deque([root])
    while q:                                  # process one level at a time
        level = []
        for _ in range(len(q)):
            node = q.popleft()
            level.append(node.val)
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        out.append(level)
    return out                                 # O(V) time, O(V) space
```

**Binary search on the answer (the senior trick) — Python:** many "minimise the maximum" problems are binary search in disguise.
```python
def min_largest_split(nums, k):
    def feasible(cap):                         # can we split into <= k parts each <= cap?
        parts, cur = 1, 0
        for n in nums:
            if cur + n > cap:
                parts += 1; cur = 0
            cur += n
        return parts <= k
    lo, hi = max(nums), sum(nums)
    while lo < hi:                             # O(n log(sum)) — search the answer space
        mid = (lo + hi) // 2
        if feasible(mid): hi = mid
        else: lo = mid + 1
    return lo
```

**Prep plan (2 weeks, ~45 min/day):** arrays/hashing → two-pointers/sliding-window → binary search → trees/BFS/DFS → heaps → intro DP. A handful of problems per pattern, done well and re-derived, beats hundreds skimmed.

---

## Format 2 — feature-building

The "build a small working thing in 45–90 minutes" round — an API endpoint, a React component, a small ETL, a mini CRUD. This is my home turf; it's what [Full-Stack Hands-On](14-fullstack-hands-on.md) and the deep-dives ([15](15-deepdive-dotnet.md)/[16](16-deepdive-react-typescript.md)/[17](17-deepdive-python-data.md)) already cover in code. The scoring is different from DSA — they watch **how I structure real code**.

### What they score (and how I win each)

| They look for | How I show it |
|---|---|
| **Structure** | Layers: thin controller → service → data ([F1](14-fullstack-hands-on.md#f1--build-a-clean-aspnet-core-web-api-endpoint)); component → hook → API ([F5](14-fullstack-hands-on.md#f5--build-a-react-data-screen)) |
| **Edge cases** | Empty, error, invalid input, not-found handled deliberately — the four states |
| **Validation** | At the boundary (Pydantic / DTO / Zod), and re-validated server-side |
| **Error handling** | One place per layer, safe message out, detail logged ([F10](14-fullstack-hands-on.md#f10--how-do-you-handle-errors-across-the-stack)) |
| **Tests** | At least the happy path + one edge, in the real framework ([F11](14-fullstack-hands-on.md#f11--how-do-you-test-your-code)) |
| **Naming & clarity** | Small functions, honest names, no dead code |
| **Communication** | Narrate decisions and trade-offs as I build |

### My feature-building playbook (45–90 min)

1. **Clarify scope** — what's the minimum that must work? Cut ruthlessly; say what I'm deferring.
2. **Sketch the shape** — layers/contract first (endpoint signature, component props, data model).
3. **Walking skeleton** — get one end-to-end path working (happy path) before polishing.
4. **Handle the edges** — empty/error/invalid; this is where seniors separate from juniors.
5. **One test** — happy path + one edge, in the real framework.
6. **Narrate trade-offs** — "I'd add caching/paging/auth here in production; skipping for time."

> The senior signal here: *a walking skeleton first, edges handled, and honesty about what I deferred and why.* I don't gold-plate; I build the smallest correct thing and name the next steps.

### Feature drill list

Time-boxed reps — each maps to code I already have:

- **Web API CRUD endpoint** with validation + error handling + a test → [F1](14-fullstack-hands-on.md#f1--build-a-clean-aspnet-core-web-api-endpoint), [F10](14-fullstack-hands-on.md#f10--how-do-you-handle-errors-across-the-stack), [F11](14-fullstack-hands-on.md#f11--how-do-you-test-your-code)
- **React screen** that fetches and renders the four states → [F5](14-fullstack-hands-on.md#f5--build-a-react-data-screen), [R4](16-deepdive-react-typescript.md#r4--useeffect-done-right)
- **Small FastAPI ingest** with Pydantic validation + idempotent load → [F4](14-fullstack-hands-on.md#f4--write-a-fastapi-etl-ingestion-endpoint), [P4](17-deepdive-python-data.md#p4--idempotent-loads-and-reconciliation)
- **Fix an N+1** on a given screen → [F3](14-fullstack-hands-on.md#f3--entity-framework-or-dapper-show-me), [D3](15-deepdive-dotnet.md#d3--linq-deferred-execution-and-the-traps)
- **Rewrite a slow query** to be sargable/set-based → [F8](14-fullstack-hands-on.md#f8--write-the-sql-not-just-design-it), [P5](17-deepdive-python-data.md#p5--sql-tuning-and-sargability)
- **Debug a failing feature** live → [F12](14-fullstack-hands-on.md#f12--walk-me-through-debugging-a-production-issue-in-code)

---

## Common mistakes I avoid

In both formats, the avoidable losses:

- **Coding before clarifying** — I always restate and ask about edges first.
- **Silence** — they can't score reasoning they can't hear; I narrate throughout.
- **Ignoring edges** — empty/null/one-item/duplicates/overflow; I test them out loud.
- **No complexity statement** (DSA) — I say time and space every time.
- **Gold-plating** (feature) — I build the smallest correct thing, then name the next steps.
- **Not testing** — I always run through examples; in feature rounds I write at least one real test.
- **Panicking when stuck** — I fall back to brute force first, state its complexity, then optimise. A working slow answer beats an elegant broken one.

**The one-line frame for the whole round:** *"Clarify, state approach and complexity, build clean, test the edges, and say how I'd productionise it — that last step is where 19 years shows."*

---

[← Deep Dive: Python & Data](17-deepdive-python-data.md) · [Home](README.md) · [Next → Cheat Sheets](08-cheatsheets.md)
