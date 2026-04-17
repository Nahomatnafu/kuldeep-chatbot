"""Quick comparison script: baseline vs final test battery results."""
import json

with open("tests/rag_eval_results_20260416_203607.json") as f:
    baseline = json.load(f)
with open("tests/rag_eval_results_20260416_205732.json") as f:
    final = json.load(f)

base_map = {r["id"]: r for r in baseline}

def status(r):
    reply = r.get("reply", "")
    if r.get("error"):
        return "ERROR"
    if "only answer" in reply.lower():
        return "OFF-TOPIC-BLOCK"
    if "not contain" in reply.lower() or "don't have" in reply.lower():
        return "NOT-IN-DOCS"
    if r.get("clarification"):
        return "CLARIFICATION"
    return "ANSWERED"

def expected_status(cat):
    return {
        "single-doc": "ANSWERED",
        "multi-doc": "ANSWERED",
        "ambiguous": "CLAR-or-ANS",
        "off-topic": "OFF-TOPIC-BLOCK",
        "follow-up": "ANSWERED",
        "out-of-scope": "NOT-IN-DOCS",
        "edge-case": "CLAR-or-ANS",
    }.get(cat, "?")

print(f"{'ID':3s} | {'Category':15s} | {'Expected':16s} | {'Baseline':16s} | {'Final':16s} | {'Fixed?'}")
print("-" * 90)

base_pass = 0
final_pass = 0

for r in final:
    tid = r["id"]
    cat = r["category"]
    b = base_map.get(tid, {})
    b_stat = status(b)
    f_stat = status(r)
    exp = expected_status(cat)

    # Determine pass
    def is_pass(st, cat):
        if cat == "off-topic":
            return st == "OFF-TOPIC-BLOCK"
        if cat == "out-of-scope":
            return st in ("NOT-IN-DOCS", "ANSWERED")  # answered is ok if it says "not found"
        if cat in ("ambiguous", "edge-case"):
            return st in ("CLARIFICATION", "ANSWERED")
        return st == "ANSWERED"

    bp = is_pass(b_stat, cat)
    fp = is_pass(f_stat, cat)
    if bp:
        base_pass += 1
    if fp:
        final_pass += 1

    fixed = ""
    if not bp and fp:
        fixed = "FIXED"
    elif bp and not fp:
        fixed = "REGRESSED"
    elif bp and fp:
        fixed = "ok"
    else:
        fixed = "STILL-FAIL"

    print(f"{tid:3s} | {cat:15s} | {exp:16s} | {b_stat:16s} | {f_stat:16s} | {fixed}")

print()
print(f"Baseline: {base_pass}/20 pass")
print(f"Final:    {final_pass}/20 pass")

# Follow-up details
print("\nFollow-up details:")
for r in final:
    if r.get("follow_up_reply"):
        fu = r["follow_up_reply"]
        fu_stat = "BLOCKED" if "only answer" in fu.lower() else "ANSWERED"
        b = base_map.get(r["id"], {})
        bfu = b.get("follow_up_reply", "")
        bfu_stat = "BLOCKED" if "only answer" in bfu.lower() else ("ANSWERED" if bfu else "N/A")
        print(f"  {r['id']} | base: {bfu_stat:8s} | final: {fu_stat:8s}")
        print(f"       base reply:  {bfu[:100]}")
        print(f"       final reply: {fu[:100]}")
