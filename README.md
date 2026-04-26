# Text-Simplification-ISC

## Workflow (MoA)

The graph now follows a Draft-Select-Audit-Edit loop:

1. Parallel Drafters: generate 4 candidate simplifications (A/B/C/D).
2. The Judge: selects the best style candidate and sets it as active text.
3. Parallel Auditors:
- Fact Checker validates numerical/clinical fidelity.
- Readability Evaluator validates accessibility and metrics.
4. The Editor: applies only the latest audit feedback when any auditor rejects.
5. Loop guard: the editor/auditor loop stops at 3 iterations.

This wiring is implemented in [src/graph/workflow.py](src/graph/workflow.py).

## Optional Model Slots

You can override model IDs per role with environment variables:

- DRAFTER_MODEL_A
- DRAFTER_MODEL_B
- DRAFTER_MODEL_C
- DRAFTER_MODEL_D
- JUDGE_MODEL
- EDITOR_MODEL

If these are not set:
- In gemini mode, default Gemini models are used per drafter.
- In ollama mode, all drafters default to OLLAMA_MODEL.

## Run With Ollama (Local LLM)

This project supports two providers:
- `gemini` (default)
- `ollama` (local)

Use Ollama mode with environment variables:

```bash
export LLM_PROVIDER=ollama
export OLLAMA_MODEL=mistral
python main.py
```

You can also enable local mode with:

```bash
export LOCAL_MODE=1
export OLLAMA_MODEL=mistral
python main.py
```

Optional:

```bash
export OLLAMA_BASE_URL=http://localhost:11434
```

In Ollama mode, `GOOGLE_API_KEY` is not required.