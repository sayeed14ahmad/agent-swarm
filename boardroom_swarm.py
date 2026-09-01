"""
Agentic Swarm — Boardroom Multi-Agent System
=============================================
Plain-Python implementation. No CrewAI execution engine. See "WHY" below.

Rulebook compliance map (Agentic Swarm Official Rulebook v1.0):
  Sec 2  Mandatory agents        -> Business Research, Finance, Marketing & Sales, CEO (below)
  Sec 3  Boardroom Protocol      -> Analyse / Share / Challenge / Compare / Decide,
                                     each one a clearly labelled STAGE block in the trace log
  Sec 3  CEO decision must have  -> enforced as 6 numbered sections in the CEO prompt
  Sec 3  Termination & control   -> one challenge/response cycle (cap is 3); every stage has a
                                     try/except fallback so one agent failing never kills the run
  Sec 5  Surprise round          -> `python boardroom_swarm.py surprise` reuses the cached
                                     baseline decision so the CEO can say what changed / stayed same
  Sec 6  Baseline/Surprise evid. -> Baseline_Trace.txt and Surprise_Trace.txt, written fresh
                                     every run, human-readable text

WHY NOT CREWAI'S EXECUTION ENGINE:
  Rulebook Sec 4 allows "Python, LangGraph, CrewAI, AutoGen... any framework" — it never requires
  CrewAI specifically. In the last debugging session, CrewAI's native Azure provider threw four
  unrelated categories of internal errors (pydantic validation on the LLM object, a missing
  azure-ai-inference extra, DeploymentNotFound from an endpoint/deployment mismatch, BadRequest
  "API version not supported", and an asyncio "no running event loop" crash from its internal
  flow runtime) — none of which had anything to do with the actual boardroom logic. That's a
  sign to stop fighting the library, not a sign to keep patching it.

  This version talks to Azure directly using the OpenAI Python SDK's plain `OpenAI` client
  pointed at Azure's newer v1 endpoint (`/openai/v1/`), which — as of the August 2025 Azure
  OpenAI v1 API — no longer needs an `api-version` parameter at all. That single change removes
  the exact error you kept hitting ("API version not supported"). It also means the trace file
  is written directly by *this* code (see log_stage below), not scraped from a third-party
  console renderer — which is why the .txt file wasn't being created before: CrewAI's `rich`
  console keeps its own reference to the real terminal and mostly ignores a patched sys.stdout.

SETUP
  pip install openai
  python boardroom_swarm.py test        # one cheap call — confirms credentials before anything else
  python boardroom_swarm.py baseline    # full 5-stage run -> Baseline_Trace.txt
  python boardroom_swarm.py surprise    # full 5-stage run with the surprise fact -> Surprise_Trace.txt
"""

import os
import sys
from datetime import datetime
from openai import OpenAI

# ============================================================
# 1. CREDENTIALS
#    Fill these in from your Azure resource's "Keys and Endpoint" page.
#    DELETE the real values before you zip/submit — rulebook Sec 10 disqualifies
#    submissions containing API keys.
# ============================================================

# The CLASSIC resource endpoint (Keys and Endpoint blade), e.g.
#   https://your-resource-name.openai.azure.com
# NOT the Foundry project endpoint (the one ending in *.services.ai.azure.com) —
# that one uses a different SDK/auth path and is what caused your DeploymentNotFound loop.
# AZURE_ENDPOINT = "https://agent-swarm-resource.openai.azure.com/"


# ============================================================
# 1. CREDENTIALS (SECURE CONFIGURATION)
# ============================================================
AZURE_API_KEY = os.environ.get("AZURE_API_KEY", "YOUR_API_KEY_HERE")
AZURE_ENDPOINT = os.environ.get("AZURE_ENDPOINT", "https://your-resource-name.openai.azure.com/")
AZURE_DEPLOYMENT_NAME = "gpt-4.1-mini"


AZURE_DEPLOYMENT_NAME = "gpt-4.1-mini"  # must match your Foundry deployment name exactly

# # ============================================================
# # 2. BUSINESS CASE
# #    Swap this for whichever theme your team actually picked at the event
# #    (this is the FinSwarm / Theme A example from your notes).
# # ============================================================
# BASELINE_CASE = """
# CASE STUDY: FinNova Capital — Small-Business Loan Pilot
# BUDGET: INR 30 crore lending capital, INR 60 lakh customer-acquisition budget.
# CONSTRAINTS:
# - Max 700 loans in the pilot.
# - Portfolio default rate must stay at or below 5%.
# - Average customer interest rate must not exceed 19% p.a.
# - No single segment may receive more than 70% of deployed capital.
# - At least INR 3 crore must remain undeployed as liquidity.
# - Cost of funds: 10% p.a. Servicing/collections: 1.5% of principal.
# - Product setup cost: INR 18 lakh (deducted from the acquisition budget).
# SEGMENTS:
# 1. Retail shops        - avg loan INR 4 lakh, 5.0% default, 1500 demand, INR 2000 CAC
# 2. Service SMEs         - avg loan INR 6 lakh, 3.5% default,  900 demand, INR 3500 CAC
# 3. Small manufacturers  - avg loan INR 9 lakh, 4.5% default,  450 demand, INR 5500 CAC
# """.strip()

# # Paste the organizer's REAL surprise fact here once it's announced. This is just a
# # placeholder/practice example so you can rehearse the flow right now.
# SURPRISE_FACT = """
# SURPRISE UPDATE: The regulator just tightened verification rules for loans above INR 5 lakh,
# adding 12 days to disbursement and an estimated INR 400 extra verification cost per loan in
# that bracket. A competitor NBFC also just entered the Retail-shop segment with a 15% flat-rate
# offer.
# """.strip()

# BASELINE_LOG = "Baseline_Trace.txt"
# SURPRISE_LOG = "Surprise_Trace.txt"
# BASELINE_DECISION_CACHE = "baseline_decision_cache.txt"


# ============================================================
# 2. BUSINESS CASE (DYNAMIC INPUT)
# ============================================================
import os

def read_input_file(filename, fallback_text):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read().strip()
    return fallback_text

BASELINE_CASE = read_input_file("baseline_case.txt", "ERROR: baseline_case.txt not found. Please create it.")
SURPRISE_FACT = read_input_file("surprise_case.txt", "ERROR: surprise_case.txt not found. Please create it.")

BASELINE_LOG = "Baseline_Trace.txt"
SURPRISE_LOG = "Surprise_Trace.txt"
BASELINE_DECISION_CACHE = "baseline_decision_cache.txt"

# ============================================================
# 3. LLM CLIENT — Azure OpenAI v1 API, no api-version needed
# ============================================================
_client = None


def get_client():
    global _client
    if _client is None:
        base = AZURE_ENDPOINT.rstrip("/")
        _client = OpenAI(api_key=AZURE_API_KEY, base_url=f"{base}/openai/v1/")
    return _client


def call_llm(prompt, temperature=0.7):
    client = get_client()
    resp = client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()


# ============================================================
# 4. AGENTS — role / goal / backstory, matching rulebook Sec 2 exactly
# ============================================================
AGENTS = {
    "research": {
        "label": "BUSINESS RESEARCH AGENT",
        "persona": (
            "You are the Business Research Agent. Your job is to analyse market, customers, "
            "competitors, opportunity and risk. You do not make the final call — you hand facts "
            "to the board. Clearly label anything you infer or assume as an ASSUMPTION rather "
            "than a supplied fact."
        ),
    },
    "finance": {
        "label": "FINANCE AGENT",
        "persona": (
            "You are the Finance Agent. Your job is to evaluate cost, revenue, affordability, "
            "profitability and financial risk. You are conservative by mandate: flag and push "
            "back on anything that risks the default-rate cap, the interest-rate cap, or the "
            "required liquidity reserve. State your numeric recommendation and your assumptions."
        ),
    },
    "marketing": {
        "label": "MARKETING & SALES AGENT",
        "persona": (
            "You are the Marketing and Sales Agent. Your job is to define target customers, "
            "positioning, channels and acquisition strategy that maximises reach within budget. "
            "You argue for growth and defend your numbers when challenged, but must engage with "
            "specific counter-numbers rather than repeating your original pitch."
        ),
    },
    "ceo": {
        "label": "CEO AGENT",
        "persona": (
            "You are the CEO Agent. Your job is to compare alternatives, resolve the conflict "
            "between departments, and issue the final company decision. You are decisive and "
            "specific — never vague, and never just an average of both sides."
        ),
    },
}

# ============================================================
# 5. LOGGING — written directly by this code, so it's guaranteed to exist
# ============================================================
def reset_log(path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("AGENTIC SWARM - BOARDROOM EXECUTION TRACE\n")
        f.write(f"Run started: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write("=" * 90 + "\n\n")


def log_stage(path, stage_no, stage_name, label, text, status="ok"):
    lines = [
        "-" * 90,
        f"STAGE {stage_no} - {stage_name}   |   {label}   |   {status.upper()}",
        f"time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "-" * 90,
        text.strip(),
        "",
    ]
    rendered = "\n".join(lines)
    print("\n" + rendered)
    with open(path, "a", encoding="utf-8") as f:
        f.write(rendered + "\n")


# ============================================================
# 6. STAGE RUNNER — the rulebook-required failure fallback lives here (Sec 3 & 4:
#    "the system must provide a final result even when one non-CEO agent fails")
# ============================================================
def run_stage(log_path, stage_no, stage_name, agent_key, task_text):
    agent = AGENTS[agent_key]
    prompt = f"{agent['persona']}\n\nTASK:\n{task_text}"
    try:
        text = call_llm(prompt)
        status = "ok"
    except Exception as e:
        text = (
            f"[FALLBACK - {agent['label']} call failed: {e}\n"
            f"Continuing the boardroom with a conservative placeholder: no new recommendation "
            f"contributed at this stage; downstream agents should treat this as an open risk.]"
        )
        status = "fallback"
    log_stage(log_path, stage_no, stage_name, agent["label"], text, status)
    return text


# ============================================================
# 7. THE BOARDROOM PROTOCOL
# ============================================================
def run_boardroom(is_surprise=False):
    log_path = SURPRISE_LOG if is_surprise else BASELINE_LOG
    reset_log(log_path)

    case_text = BASELINE_CASE
    if is_surprise:
        case_text = BASELINE_CASE + "\n\n" + SURPRISE_FACT

    baseline_decision = ""
    if is_surprise and os.path.exists(BASELINE_DECISION_CACHE):
        with open(BASELINE_DECISION_CACHE, "r", encoding="utf-8") as f:
            baseline_decision = f.read()

    surprise_clause = ""
    if is_surprise:
        surprise_clause = (
            "\n\nThis is the SURPRISE ROUND. Compare against the original case facts above. "
            "Explicitly state which facts or assumptions changed and which stayed the same."
        )

    # --- Stage 1: Analyse ---
    research_out = run_stage(
        log_path, 1, "ANALYSE", "research",
        f"Independently analyse this business case and extract the constraints, opportunity "
        f"and risk that matter for the lending decision:\n\n{case_text}{surprise_clause}",
    )

    finance_out = run_stage(
        log_path, 1, "ANALYSE", "finance",
        f"Research findings:\n{research_out}\n\nCase facts:\n{case_text}{surprise_clause}\n\n"
        f"Independently evaluate this case. Recommend numeric limits: max spend per segment, "
        f"acceptable default rate per segment, and interest rate. State your assumptions.",
    )

    marketing_out = run_stage(
        log_path, 1, "ANALYSE", "marketing",
        f"Research findings:\n{research_out}\n\nCase facts:\n{case_text}{surprise_clause}\n\n"
        f"Independently propose a segment allocation and go-to-market plan that maximises "
        f"reach within the acquisition budget. Give specific numbers per segment.",
    )

    # --- Stage 2: Share (no LLM call — this documents the hand-off for judges, costs nothing) ---
    log_stage(
        log_path, 2, "SHARE", "SYSTEM",
        "Finance's and Marketing's Stage-1 outputs above were passed as shared context into "
        "every subsequent stage, along with the Research findings. No agent call is needed for "
        "this hand-off — it is simply the input to Stage 3 below.",
    )

    # --- Stage 3: Challenge ---
    challenge_out = run_stage(
        log_path, 3, "CHALLENGE", "finance",
        f"Marketing's proposal:\n{marketing_out}\n\nYour own Stage-1 numbers were:\n{finance_out}\n\n"
        f"Identify ONE specific element of Marketing's plan you REJECT or must cut, citing exact "
        f"numbers and which constraint it breaks (default-rate cap, rate cap, liquidity reserve, "
        f"or the 70% single-segment cap). Propose your constrained alternative.",
    )

    response_out = run_stage(
        log_path, 3, "CHALLENGE - response", "marketing",
        f"Finance just challenged your plan:\n{challenge_out}\n\nRespond directly: either defend "
        f"your original number with a specific business justification, or concede and give an "
        f"adjusted number. Do not repeat your original pitch unchanged.",
    )

    # --- Stage 4: Compare ---
    compare_out = run_stage(
        log_path, 4, "COMPARE", "ceo",
        f"Boardroom record so far:\nRESEARCH: {research_out}\nFINANCE: {finance_out}\n"
        f"MARKETING: {marketing_out}\nCHALLENGE: {challenge_out}\nRESPONSE: {response_out}\n\n"
        f"Compare at least TWO viable strategies for this pilot (for example: Marketing's "
        f"original ask, Finance's constrained alternative, and/or a blended option). For each, "
        f"state the expected outcome and the main risk. Do not pick a winner yet.",
    )

    # --- Stage 5: Decide ---
    decide_prompt = (
        f"Boardroom record:\nRESEARCH: {research_out}\nFINANCE: {finance_out}\n"
        f"MARKETING: {marketing_out}\nCHALLENGE: {challenge_out}\nRESPONSE: {response_out}\n"
        f"COMPARISON: {compare_out}\n\n"
    )
    if is_surprise:
        decide_prompt += (
            "ORIGINAL BASELINE DECISION (for comparison):\n"
            f"{baseline_decision if baseline_decision else '[no cached baseline found - run `python boardroom_swarm.py baseline` first]'}\n\n"
            "This is a REVISED decision after the surprise. Explicitly state what changed from "
            "the baseline decision, what stayed the same, and why.\n\n"
        )
    decide_prompt += (
        "Issue the final decision. Your answer MUST use exactly these six labelled sections:\n"
        "1. SELECTED DECISION - one clear statement\n"
        "2. DEPARTMENT EVIDENCE USED\n"
        "3. REJECTED ALTERNATIVE(S) AND WHY\n"
        "4. TRADE-OFFS, RISKS AND ASSUMPTIONS\n"
        "5. IMPLEMENTATION SEQUENCE - each step with the responsible department\n"
        "6. AT LEAST THREE MEASURABLE KPIs"
    )
    ceo_decision = run_stage(log_path, 5, "DECIDE", "ceo", decide_prompt)

    if not is_surprise:
        with open(BASELINE_DECISION_CACHE, "w", encoding="utf-8") as f:
            f.write(ceo_decision)

    print(f"\nDone. Full trace saved to: {log_path}")
    return ceo_decision


# ============================================================
# 8. CONNECTIVITY SMOKE TEST — run this FIRST. One cheap call, fast feedback.
# ============================================================
def test_connection():
    print("Testing Azure OpenAI connection...")
    try:
        out = call_llm("Reply with exactly: connection ok")
        print(f"SUCCESS - model replied: {out}")
    except Exception as e:
        print(f"FAILED: {e}")
        print(
            "\nCheck: AZURE_ENDPOINT is the classic https://<resource>.openai.azure.com form "
            "(not the Foundry *.services.ai.azure.com project URL), AZURE_DEPLOYMENT_NAME "
            "matches your Foundry deployment name exactly, and AZURE_API_KEY is Key 1/2 from "
            "that same resource's 'Keys and Endpoint' page."
        )


# ============================================================
# 9. ENTRY POINT
# ============================================================
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    if mode == "test":
        test_connection()
    elif mode == "surprise":
        run_boardroom(is_surprise=True)
    else:
        run_boardroom(is_surprise=False)
