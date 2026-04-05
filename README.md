# Text-Simplification-ISC

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