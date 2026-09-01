# FinNova Capital Boardroom Swarm

## 1. Team Information

* **Team Name:** AAAVEYY
* **Team Members:** 1) A Sayeed Ahmad; 2) Abhishek R Jeyprakash 3) Ana Christy 4) Vidyut Jayaprakash

## 2. Selected Challenge & Solution Summary

**Selected Challenge:** Theme A — FinSwarm (Digital Lending)

**Solution Summary:** Our solution implements a deterministically sequenced, plain-Python multi-agent boardroom simulation designed to solve the FinNova Capital loan deployment challenge. By decoupling case study inputs into modular external text files (`baseline_case.txt` and `surprise_case.txt`) and utilizing direct Azure OpenAI API calls, the architecture guarantees strict adherence to the mandated 5-stage protocol (Analyse, Share, Challenge, Compare, Decide). The swarm enforces genuine inter-departmental conflict—specifically between growth-focused Marketing and risk-averse Finance—forcing the CEO agent to synthesize competing data, evaluate hard liquidity and default constraints, and output a structured, compliant executive decision with measurable KPIs.

## 3. Agent List: Roles, Inputs, and Outputs

* **Business Research Agent**
* **Role:** Analytical purist focused on extracting core data trends and structural bottlenecks.
* **Input:** Raw case constraints loaded dynamically from `baseline_case.txt`, capital limits, and segment demand parameters.


* **Output:** A baseline market reality report summarizing financial caps, opportunity metrics, and segment-specific risks.


* **Finance Agent**
* **Role:** Conservative auditor mandated to enforce cost controls, minimize capital burn, and preserve the INR 3 crore liquidity reserve.


* **Input:** Research report, baseline case facts, and subsequently, the Marketing Agent's initial deployment proposal.
* **Output:** Numeric recommendations for capital limits, followed by a formal challenge/rejection of any Marketing proposal that breaches risk or liquidity thresholds.


* **Marketing & Sales Agent**
* **Role:** Aggressive growth advocate focused on maximizing user acquisition velocity and loan deployment.


* **Input:** Research report, baseline case facts, and subsequently, the Finance Agent's challenge.
* **Output:** A high-spend/high-reach segment allocation plan, followed by an adjusted counter-proposal defending business growth within newly conceded financial constraints.


* **CEO Agent**
* **Role:** Final executive decision-maker responsible for mediating deadlock and establishing a single execution directive.
* **Input:** The complete STAGE 1–3 trace log (Research data, Finance limits, Marketing proposals, and the Challenge/Response debate).
* **Output:** A 6-section Executive Order detailing the selected strategy, rejected paths, trade-offs/assumptions, implementation roadmap, and exactly 3 measurable KPIs.



## 4. Installation and Execution Instructions

**Prerequisites:** Python 3.8+

**Installation:**

```bash
# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the required OpenAI SDK
pip install openai

```

**Configuration:**
Before running, open `boardroom_swarm.py` and replace the placeholder credentials at the top of the file with your active Azure values. *Ensure the API key is removed before final repository submission.*

```python
AZURE_API_KEY = "your_actual_api_key"
AZURE_ENDPOINT = "https://your-resource-name.openai.azure.com"
AZURE_DEPLOYMENT_NAME = "gpt-4.1-mini"

```

**Execution:**
Ensure that `baseline_case.txt` (containing the case study facts) and `surprise_case.txt` are present in the project root directory. The system uses a single entry point with distinct arguments for testing and execution:

```bash
# 1. Test connectivity and credentials
python boardroom_swarm.py test

# 2. Run the baseline scenario (outputs to Baseline_Trace.txt)
python boardroom_swarm.py baseline

# 3. Run the surprise round scenario (outputs to Surprise_Trace.txt)
python boardroom_swarm.py surprise

```

## 5. Models, Frameworks, Datasets, and External Services

* **Core Model:** Azure OpenAI `gpt-4.1-mini`.
* **Framework:** Custom plain-Python sequential execution framework with dynamic text-file input reading. We intentionally excluded heavy orchestration frameworks to maintain absolute control over the STAGE logging mechanism and prevent API versioning conflicts with the Azure v1 endpoint.
* **Libraries:** Standard `openai` Python SDK (v1.0+).
* **Datasets:** None. All data is synthetically derived from the provided Theme A (FinSwarm) test cases.


* **External Services:** Azure OpenAI Services for LLM inference.

## 6. Known Limitations and Failure-Handling Behaviour

**Failure-Handling Behaviour:**
The architecture is specifically designed to satisfy the rulebook requirement of surviving individual agent failures. Every STAGE execution is wrapped in a `try/except` block. If an LLM call fails (due to API timeouts, token limits, or network drops), the system catches the exception, logs the error, and automatically injects a conservative fallback placeholder into the boardroom record. This ensures downstream agents still receive inputs and the CEO Agent can always produce a final decision, preventing total system collapse.

**Known Limitations:**

* **Rigid Sequencing:** The 5-stage STAGE protocol is hardcoded to fire sequentially (Research → Finance/Marketing → Challenge → Compare → Decide) to guarantee compliance. It does not support dynamic, infinitely looping debate.
* **Context Window Reliance:** All previous STAGE outputs are appended to the context window of the CEO. At extreme token lengths, truncation could theoretically occur, though the current FinNova constraints keep prompt sizes well within safety margins.

## 7. Declaration of Pre-Existing or Reused Components

The core multi-agent execution loop, stage logging mechanism, dynamic text-file input reading, and prompt structures were custom-built entirely during this hackathon to meet the explicit guidelines of the Agentic Swarm Official Rulebook. The implementation utilizes the standard OpenAI Python SDK for API connectivity. No pre-existing proprietary templates, external agentic libraries (CrewAI/AutoGen), or unauthorized third-party boilerplates were used in the creation of the swarm logic.