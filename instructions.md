# Multi-Agent Architecture Specification: Medical Simplifier (Task 1.2)
**Framework:** LangGraph
**Objective:** Simplify complex biomedical abstracts into Plain Language through a "Draft-Select-Audit-Edit" workflow using Mixture of Agents (MoA).

## 1. Nodes (Agents) and Responsibilities

### Node 1: `Parallel_Drafters` (Draft Generation)
- **Execution:** Asynchronous/Parallel.
- **Input:** `complex_text` + Rich System Prompt (Glossary and Rules).
- **Models (via APIs):** Mistral Small 4, DeepSeek v4 Flash, Llama 3.3 70B, Gemini 2.5 Flash Lite.
- **Output:** Generates 4 texts and saves them in the `drafts` dictionary (A, B, C, D).

### Node 2: `The_Judge` (Style Selector)
- **Model:** Gemini 2.5 Flash.
- **Input:** `complex_text` and `drafts`.
- **Prompt:** "You act as a Plain Language Style Judge. Evaluate options A, B, C, and D against the original text according to the plain language manual provided. DO NOT evaluate numerical accuracy. You must output at the very end: 'WINNER: [Letter]'."
- **Output:** Extracts the winning letter, saves it in `selected_draft_letter`, and copies the corresponding text from the `drafts` dictionary into `current_simplified_text`.

### Node 3: `Parallel_Auditors` (Auditing Phase)
Executes two parallel validations on `current_simplified_text`:

#### Auditor 3.1: `Fact_Checker`
- **Model:** Mistral Small 4.
- **Input:** `complex_text` vs `current_simplified_text`.
- **Output:** If numerical and clinical data are 100% accurate, sets `is_fact_approved = True`. If there are inconsistencies, sets it to `False` and appends the error report to `feedback_history`.

#### Auditor 3.2: `Readability_Evaluator` (via MCP)
- **Model:** Gemini 2.5 Flash + MCP Server.
- **Input:** Calls MCP tools (e.g., `calculate_flesch_kincaid`) on `current_simplified_text`.
- **Output:** Saves the tool results in `current_metrics`. If it meets the required readability metrics, sets `is_readability_approved = True`. If not, sets it to `False` and appends the improvement feedback to `feedback_history`.

### Node 4: `The_Editor` (Correction Phase)
- **Model:** Gemini 2.5 Flash.
- **Input:** `current_simplified_text` + latest feedback in `feedback_history`.
- **Prompt:** "Correct the simplified text based SOLELY on this audit feedback. Keep the rest of the text intact."
- **Output:** Updates `current_simplified_text` with the corrected version and increments `iteration_count` by +1.

## 2. Routing Logic (Conditional Edges)
1. `START` -> `Parallel_Drafters`
2. `Parallel_Drafters` -> `The_Judge`
3. `The_Judge` -> `Parallel_Auditors`
4. **Conditional Edge from `Parallel_Auditors`:**
   - If `is_fact_approved` == True **AND** `is_readability_approved` == True -> Route to `END`.
   - If any of them is False **AND** `iteration_count` < 3 -> Route to `The_Editor`.
   - If `iteration_count` >= 3 -> Route to `END` (Safety mechanism to prevent infinite loops).
5. `The_Editor` -> Loops back to `Parallel_Auditors`.