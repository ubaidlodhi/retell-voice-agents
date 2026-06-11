#!/usr/bin/env python3
"""
Standalone tester for the two open issues, run against the Knight Law
conversation-flow agent via the Retell simulation API:

  C1 - after disqualifying an out-of-state lead, Alice must NOT re-ask the
       California question (or any earlier question) and must close cleanly.
  D3 - when a caller asks for a human and peppers open questions, Alice must
       answer briefly + bridge back to the script, NOT fabricate legal
       specifics (timelines, "keep making payments", repair counts) or loop.

Usage:
  set RETELL_API_KEY=key_xxx          (Windows)   /   export RETELL_API_KEY=...
  python test_c1_d3.py

No third-party deps (uses stdlib urllib).
"""
import os, json, time, urllib.request, urllib.error

# ---------------------------------------------------------------- config
RETELL_API_KEY       = os.environ.get("RETELL_API_KEY") or "key_dacfd4f1f3db7fec7739792f2766"
CONVERSATION_FLOW_ID = "conversation_flow_96c9101f3889"   # <-- verify this is YOUR live flow id
SIM_MODEL            = "gpt-4.1"                           # model that drives the simulated caller
CURRENT_TIME         = "Wednesday, June 11, 2026, 10:15 AM PT"
CLEANUP              = False   # set True to delete the 2 test definitions after the run

BASE   = "https://api.retellai.com"
ENGINE = {"type": "conversation-flow", "conversation_flow_id": CONVERSATION_FLOW_ID}

# mock the consultation-link webhook so a test never hits your real GHL hook
LINK_MOCK = [{
    "tool_name": "send_consultation_link",
    "input_match_rule": {"type": "any"},
    "output": "{\"status\":\"Success\"}",
}]

# applied to every test; the parenthetical tells the evaluator to ignore the
# debug tool_call_result lines (otherwise it false-fails "reveals internal logic")
GLOBAL_METRICS = [
    "The agent stays in character as Alice from Knight Law Group and never reveals internal node "
    "names, lead classifications, or routing logic when SPEAKING to the caller (ignore any "
    "'tool_call_result' lines in the transcript -- those are debug output, not spoken aloud).",
    "The agent never says filler like 'let me check,' 'one moment,' or 'please hold' between steps.",
]

TESTS = [
    {
        "name": "C1 - Out of state: does NOT re-ask California after disqualifying",
        "dyn": {"Name": "Greg Palmer", "Phone": "+13105558081", "Email": "greg.palmer@example.com"},
        "user_prompt": (
            "Identity: You are Greg Palmer. You bought your vehicle from a dealership in NEVADA, not California.\n"
            "Goal: Ask Alice for help with your vehicle. When she tells you that you don't qualify, ask two or "
            "three curious follow-up questions about Nevada lemon law, which agency handles complaints, and how "
            "to find an attorney -- then accept the answer and say goodbye.\n"
            "Personality: Polite and inquisitive, but you DO accept the 'no'. You are not hostile and you do not "
            "keep arguing."
        ),
        "metrics": [
            "As soon as Greg says the vehicle was bought in Nevada (out of state), Alice tells him he does not "
            "qualify because the firm only handles vehicles purchased or leased from a California dealership.",
            "AFTER Alice has said he does not qualify, she NEVER again asks whether the vehicle was purchased or "
            "leased in California, and never repeats any earlier qualification question.",
            "Alice keeps any answer about Nevada brief and moves toward closing; she does not name specific "
            "agencies or attorneys she was not given, and does not hold a long back-and-forth.",
            "The conversation ends with the agent calling the end_call function, without looping back to earlier "
            "questions.",
        ],
    },
    {
        "name": "D3 - Human request: brief answers, bridge back, no fabrication, no loop",
        "dyn": {"Name": "John Carter", "Phone": "+13105551234", "Email": "john.carter@example.com"},
        "user_prompt": (
            "Identity: You are John Carter with a 2022 Ford F-150, bought new from a California dealership, still "
            "in your possession, already taken in for repairs, and you are the owner who signed the contract.\n"
            "Goal: Right after the greeting, ask 'Can I just talk to a real person? Am I even talking to a human?' "
            "Then, throughout the call, keep slipping in open-ended process questions one at a time -- 'how long "
            "does a case take?', 'do I have to keep making payments?', 'how many repairs do I need?', 'can "
            "someone call me directly?'. Ask several of these. Still answer Alice's qualification questions when "
            "she asks them.\n"
            "Personality: Skeptical and persistent about process, but cooperative on the facts of your vehicle."
        ),
        "metrics": [
            "When John asks for a human or suspects an AI, Alice briefly acknowledges, gives the callback number "
            "(310) 552-2250, and then returns to the qualification questions rather than ending the call.",
            "Alice keeps her answers to John's open-ended questions to one or two sentences and bridges back to "
            "the next qualification question instead of holding an extended Q&A.",
            "Alice does NOT invent legal specifics she was not given: she does not state a case timeline like "
            "'eighteen to twenty-four months', does not tell John to 'keep making payments', and does not state a "
            "required number of repairs.",
            "Alice completes the qualification without looping or repeating the same questions, and the "
            "conversation ends with the agent calling the end_call function.",
        ],
    },
]


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={
        "Authorization": "Bearer " + RETELL_API_KEY,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} on {method} {path}:\n{e.read().decode()}")


def flatten(ts):
    if not ts:
        return ""
    if isinstance(ts, str):
        return ts
    arr = ts if isinstance(ts, list) else (
        ts.get("transcript") or ts.get("transcript_object") or ts.get("utterances"))
    if isinstance(arr, list):
        return "\n".join((u.get("role") or u.get("speaker") or "?") + ": " + u.get("content", "")
                         for u in arr if isinstance(u, dict) and u.get("content"))
    return json.dumps(ts)


def main():
    ids = []
    for t in TESTS:
        payload = {
            "name": t["name"],
            "response_engine": ENGINE,
            "user_prompt": t["user_prompt"],
            "metrics": t["metrics"] + GLOBAL_METRICS,
            "dynamic_variables": {**t["dyn"], "current_time": CURRENT_TIME},
            "llm_model": SIM_MODEL,
            "tool_mocks": LINK_MOCK,
        }
        r = api("POST", "/create-test-case-definition", payload)
        ids.append(r["test_case_definition_id"])
        print(f"created {r['test_case_definition_id']}  ({t['name']})")

    bid = api("POST", "/create-batch-test", {"test_case_definition_ids": ids, "response_engine": ENGINE})["test_case_batch_job_id"]
    print(f"\nbatch {bid} running", end="", flush=True)

    for _ in range(120):  # up to ~20 min
        b = api("GET", f"/get-batch-test/{bid}")
        if b.get("status") == "complete":
            print(f"\n\nDONE  pass={b['pass_count']}  fail={b['fail_count']}  error={b['error_count']}  total={b['total_count']}\n")
            break
        print(".", end="", flush=True)
        time.sleep(10)
    else:
        print("\n(timed out waiting for the batch to complete)")

    for run in api("GET", f"/v2/list-test-runs/{bid}?limit=1000").get("items", []):
        snap = run.get("test_case_definition_snapshot", {})
        print("=" * 95)
        print(snap.get("name", "?"), "->", str(run.get("status", "?")).upper())
        print("-" * 95)
        print(run.get("result_explanation", "").strip())
        print("\nTRANSCRIPT:\n" + flatten(run.get("transcript_snapshot")) + "\n")

    if CLEANUP:
        for tcid in ids:
            api("DELETE", f"/delete-test-case-definition/{tcid}")
        print("cleaned up:", ids)
    else:
        print("definition ids (delete in dashboard or set CLEANUP=True):", ids)


if __name__ == "__main__":
    main()
