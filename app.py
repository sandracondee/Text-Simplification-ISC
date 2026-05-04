import asyncio
import html
import re
import os
from typing import Any, Dict

import base64
import streamlit.components.v1 as components

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from src.workflow import build_graph

load_dotenv()


st.set_page_config(
    page_title="Medical Plain Language Simplifier",
    page_icon="🩺",
    layout="wide",
)

def get_local_img_as_base64(file_path: str) -> str:
    """Lee un archivo de imagen local y lo convierte a Base64."""
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


CUSTOM_CSS = """
<style>
    .block-container {
        padding-top: 0.5rem !important; /* Puedes bajarlo a 1rem o incluso 0rem si lo quieres pegado del todo */
        padding-bottom: 3rem !important; /* Aprovechamos para reducir también el espacio del fondo */
    }
    .app-shell {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }

    main {
        padding-top: 0rem !important;
    }

    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] > [data-testid="stMarkdown"]:first-child {
        margin-top: -1rem;
    }

    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }

    .text-panel {
        border-radius: 0.8rem;
        padding: 1rem;
        line-height: 1.65;
        min-height: 100px;
        word-wrap: break-word;
        background: #ADAF7E;
        color: #31333F;
    }

    .stButton > button {
        background-color: #ADAF7E; /* Tu color secundario */
        color: #31333F;             /* Color del texto */
        border: 2px solid rgba(0, 0, 0, 1);  /* Borde negro de 2px */
    }

    .stButton > p {
        margin: 0; /* Asegura que el texto esté centrado */
    }

    .stButton > button, .stFormSubmitButton > button {
        background-color: #ADAF7E; /* Tu color secundario */
        color: #31333F;             /* Color del texto */
        border: none !important;    /* Quitamos el borde */
        transition: background-color 0.2s ease, color 0.2s ease; /* Transición suave */
    }

    /* Efecto al pasar el ratón por encima (Hover) */
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background-color: #454632 !important; /* Fondo oscuro */
        color: #EDEDE9 !important;             /* Texto clarito (casi blanco) */
    }

    /* --- DISEÑO DE TIMELINE (Línea de tiempo del proceso) --- */
    .timeline-wrapper {
        position: relative;
        padding-left: 45px;
        margin-top: 1rem;
        margin-bottom: 2rem;
    }

    /* La línea vertical que une a los agentes */
    .timeline-wrapper::before {
        content: '';
        position: absolute;
        left: 18px;
        top: 0;
        bottom: 0;
        width: 4px;
        background-color: #ADAF7E; /* Tu color verde base */
        border-radius: 2px;
        opacity: 0.6;
    }

    .stream-card {
        position: relative;
        background-color: #EDEDE9; /* <-- Tu nuevo color de fondo */
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        border-radius: 0.6rem;
        border: 1px solid rgba(173, 175, 126, 0.4); 
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04); 
        color: #454632; /* Forzamos texto oscuro para contraste perfecto */
    }

    /* El círculo flotante en la línea de tiempo */
    .stream-card::before {
        content: '';
        position: absolute;
        left: -33px; /* Centrado matemáticamente sobre la línea */
        top: 1.3rem;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background-color: white;
        border: 4px solid #ADAF7E;
        z-index: 1;
    }

    /* Títulos convertidos en etiquetas (Badges) */
    .stream-card h4 {
        display: inline-block;
        margin: 0 0 0.6rem 0;
        padding: 0.35rem 0.85rem;
        border-radius: 2rem; /* Bordes redondeados estilo pastilla */
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        color: white;
        letter-spacing: 0.5px;
    }

    .stream-card p {
        margin: 0;
        white-space: pre-wrap;
        line-height: 1.6;
        font-size: 0.95rem;
    }

    /* --- COLORES VIBRANTES POR AGENTE --- */
    
    /* Parallel drafters */
    .card-parallel-drafters::before { border-color: #5B9ECF; }
    .card-parallel-drafters h4 { background-color: #5B9ECF; color: #EDEDE9; }

    /* Fact checker */
    .card-fact-checker::before { border-color: #C8AA10; }
    .card-fact-checker h4 { background-color: #C8AA10; color: #EDEDE9; } /* Texto oscuro para mejor contraste */

    /* Judge */
    .card-judge::before { border-color: #7F67A1; }
    .card-judge h4 { background-color: #7F67A1; color: #EDEDE9; }

    /* Readability evaluator */
    .card-readability-evaluator::before { border-color: #BF870E; }
    .card-readability-evaluator h4 { background-color: #BF870E; color: #EDEDE9; }

    /* Guardrail */
    .card-guardrail::before { border-color: #D97706; }
    .card-guardrail h4 { background-color: #D97706; color: #EDEDE9; }

    /* Term explainer */
    .card-term-explainer::before { border-color: #70965D; }
    .card-term-explainer h4 { background-color: #70965D; color: #EDEDE9; }

    /* Editor */
    .card-editor::before { border-color: #A9452B; }
    .card-editor h4 { background-color: #A9452B; color: #EDEDE9; }
    
    /* Auditor Aggregator / Default */
    .card-auditors::before { border-color: #4A5568; }
    .card-auditors h4 { background-color: #4A5568; color: #EDEDE9; }


    .tooltip {
        position: relative;
        display: inline;
        /* Quitamos la línea de abajo que tenías antes */
        /* border-bottom: 1px dotted var(--primary-color, #0b6efd); */
        
        /* Efecto subrayador verde oscuro */
        background-color: #8C9364; /* Un verde más oscuro que tu fondo #ADAF7E */
        padding: 0.1rem 0.3rem;    /* Espacio extra para que el color sobresalga de la palabra */
        border-radius: 0.25rem;    /* Bordes ligeramente redondeados */
        color: #31333F;            /* Mantenemos el color de texto oscuro */
        cursor: help;
        font-weight: 600;
        transition: background-color 0.2s ease; /* Transición suave */
    }

    /* Opcional: Un pequeño efecto para que se oscurezca un poco más al pasar el ratón */
    .tooltip:hover {
        background-color: #788053; 
    }

    /* Light mode tooltips */
    @media (prefers-color-scheme: light) {
        .tooltip .tooltiptext {
            visibility: hidden;
            opacity: 0;
            transition: opacity 0.18s ease-in-out;
            position: absolute;
            left: 50%;
            bottom: calc(100% + 0.7rem);
            transform: translateX(-50%);
            z-index: 9999;
            width: max-content;
            max-width: min(24rem, 82vw);
            padding: 0.7rem 0.85rem;
            border-radius: 0.75rem;
            border: 1px solid rgba(100, 100, 100, 0.3);
            background: #f8f9fa;
            color: #212529;
            box-shadow: 0 0.5rem 1.3rem rgba(0, 0, 0, 0.15);
            font-weight: 400;
            line-height: 1.45;
            pointer-events: none;
        }

        .tooltip .tooltiptext::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border-width: 0.45rem;
            border-style: solid;
            border-color: #f8f9fa transparent transparent transparent;
        }
    }

    /* Dark mode tooltips */
    @media (prefers-color-scheme: dark) {
        .tooltip .tooltiptext {
            visibility: hidden;
            opacity: 0;
            transition: opacity 0.18s ease-in-out;
            position: absolute;
            left: 50%;
            bottom: calc(100% + 0.7rem);
            transform: translateX(-50%);
            z-index: 9999;
            width: max-content;
            max-width: min(24rem, 82vw);
            padding: 0.7rem 0.85rem;
            border-radius: 0.75rem;
            border: 1px solid rgba(200, 200, 200, 0.25);
            background: #454632;
            color: #EDEDE9;
            box-shadow: 0 0.5rem 1.3rem rgba(0, 0, 0, 0.3);
            font-weight: 400;
            line-height: 1.45;
            pointer-events: none;
        }

        .tooltip .tooltiptext::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border-width: 0.45rem;
            border-style: solid;
            border-color: #454632 transparent transparent transparent;
        }
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }

    .muted-note {
        opacity: 0.72;
        font-size: 0.95rem;
    }

    /* Transformar los botones secundarios en tarjetas de texto (para los ejemplos) */
    button[data-testid="baseButton-secondary"] {
        min-height: 240px; /* Altura mínima de la tarjeta */
        height: 100%;      /* Para que todos midan lo mismo en la misma fila */
        align-items: flex-start; /* Empuja el texto hacia arriba */
        padding: 1.2rem;
    }

    button[data-testid="baseButton-secondary"] p {
        white-space: pre-wrap; /* Permite que el texto baje de línea */
        text-align: left;      /* Alinea a la izquierda para mejor lectura */
        line-height: 1.5;
        font-size: 0.95rem;    /* Hace la fuente un pelín más pequeña si hace falta */
    }
</style>
"""


DEFAULT_COMPLEX_TEXT = ""


DEFAULT_REFERENCE_TEXT = ""


def get_graph():
    """Build the compiled LangGraph once per Streamlit session."""
    return build_graph()


@st.cache_data
def load_examples() -> list[Dict[str, str]]:
    """Load examples from the CSV file."""
    try:
        csv_path = os.path.join(os.path.dirname(__file__), "data", "cochraneauto_docs_test.csv")
        df = pd.read_csv(csv_path)
        examples = []
        for idx, row in df.iterrows():
            examples.append({
                "id": idx,
                "pair_id": row.get("pair_id", f"Example {idx+1}"),
                "complex": row["complex"],
                "simple": row["simple"]
            })
        return examples
    except Exception as e:
        st.warning(f"Could not load examples: {e}")
        return []


def humanize_node_name(node_name: str) -> str:
    labels = {
        "guardrail": "Input Guardrail",
        "parallel_drafters": "Parallel Simplifiers",
        "judge": "Judge",
        "fact_checker": "Fact Checker",
        "readability_evaluator": "Readability Evaluator",
        "editor": "Editor",
        "term_explainer": "Term Explainer",
        "auditors": "Auditor Aggregator",
    }
    return labels.get(node_name, node_name.replace("_", " ").title())


def safe_text_block(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


def apply_tooltips(text: str, term_explanations: Dict[str, Dict[str, str]]) -> str:
    """Wrap detected terms in tooltip spans while keeping the text HTML-safe."""
    if not text:
        return ""

    if not term_explanations:
        return safe_text_block(text)

    ordered_terms = sorted(term_explanations.keys(), key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(term) for term in ordered_terms), re.IGNORECASE)

    pieces = []
    last_index = 0

    for match in pattern.finditer(text):
        start, end = match.span()
        pieces.append(html.escape(text[last_index:start]))
        matched_text = match.group(0)

        matched_entry = None
        for term in ordered_terms:
            if term.lower() == matched_text.lower():
                matched_entry = term_explanations.get(term)
                break

        if matched_entry:
            dictionary_term = html.escape(matched_entry.get("dictionary_term", matched_text))
            explanation = html.escape(matched_entry.get("explanation", ""))
            safe_term = html.escape(matched_text)
            pieces.append(
                "<span class='tooltip'>"
                f"{safe_term}"
                "<span class='tooltiptext'>"
                f"<strong>{dictionary_term}</strong><br>{explanation}"
                "</span></span>"
            )
        else:
            pieces.append(html.escape(matched_text))

        last_index = end

    pieces.append(html.escape(text[last_index:]))
    return "".join(pieces).replace("\n", "<br>")


def render_text_panel(title: str, content_html: str, original: bool = False) -> None:
    panel_class = "text-panel is-original" if original else "text-panel"
    st.markdown(
        f"<div class='section-title'>{html.escape(title)}</div>"
        f"<div class='{panel_class}'>{content_html}</div>",
        unsafe_allow_html=True,
    )


def render_stream_card(title: str, body: str, node_id: str = "default", escape_body: bool = True) -> str:
    css_class = f"stream-card card-{node_id.replace('_', '-')}"
    # Solo escapamos si se lo pedimos, si no, respetamos el HTML que le pasemos
    formatted_body = html.escape(body).replace('\n', '<br>') if escape_body else body
    return (
        f"<div class='{css_class}'>"
        f"<h4>{html.escape(title)}</h4>"
        f"<p>{formatted_body}</p>"
        "</div>"
    )


def format_metrics(metrics: Dict[str, Any]) -> str:
    if not metrics:
        return "No metrics reported yet."

    lines = []
    for metric, value in metrics.items():
        if isinstance(value, float):
            lines.append(f"{metric}: {value:.2f}")
        else:
            lines.append(f"{metric}: {value}")
    return "\n".join(lines)


def format_update_card(node_name: str, updates: Dict[str, Any], final_state: Dict[str, Any]) -> str:
    if node_name == "guardrail":
        in_scope = updates.get("is_input_in_scope", True)
        rationale = updates.get("guardrail_rationale", "")
        refusal_message = updates.get("guardrail_message", "")
        verdict = "✅ IN SCOPE" if in_scope else "⛔ OUT OF SCOPE"

        safe_rationale = html.escape(rationale).replace('\n', '<br>')
        body = (
            f"<details style='margin-bottom: 0.5rem; cursor: pointer;'>"
            f"  <summary style='font-weight: 600; outline: none;'>🛡️ Scope check</summary>"
            f"  <div style='margin-top: 0.5rem; padding: 0.8rem; background-color: rgba(0,0,0,0.05); border-radius: 0.4rem; font-size: 0.95em;'>"
            f"      {safe_rationale}"
            f"  </div>"
            f"</details>"
            f"<strong>Verdict: {verdict}</strong>"
        )

        if refusal_message and not in_scope:
            safe_refusal = html.escape(refusal_message).replace('\n', '<br>')
            body += f"\n\n📢 Message to user: {safe_refusal}"

        return render_stream_card("🛡️ Input Guardrail", body, node_name, escape_body=False)

    if node_name == "parallel_drafters":
        drafts = updates.get("drafts", {})
        draft_lines = []
        for letter in ["A", "B", "C", "D"]:
            draft_text = drafts.get(letter, "")
            # Acortamos un poco la previsualización para que no ocupe toda la pantalla
            preview = draft_text.replace("\n", " ")
            
            draft_lines.append(f"🔹 Draft {letter}:\n\"{preview or 'No draft returned.'}\"")
        
        body = "✨ Generated 4 independent simplifications:\n\n" + "\n\n".join(draft_lines)
        return render_stream_card("✍️ Parallel Simplifiers", body, node_name)

    if node_name == "judge":
        selected_letter = updates.get("selected_draft_letter", "")
        selected_text = updates.get("current_simplified_text", "")
        rationale = updates.get("judge_rationale", "")

        safe_rationale = html.escape(rationale).replace('\n', '<br>')
        safe_preview = html.escape(selected_text).replace('\n', '<br>')

        body = (
            f"<details style='margin-bottom: 1rem; cursor: pointer;'>"
            f"  <summary style='font-weight: 600; outline: none;'>💭 Rationale</summary>"
            f"  <div style='margin-top: 0.5rem; padding: 0.8rem; background-color: rgba(0,0,0,0.05); border-radius: 0.4rem; font-size: 0.95em;'>"
            f"      {safe_rationale}"
            f"  </div>"
            f"</details>"
            f"🏆 <strong>Selected Winner: Draft {selected_letter or 'N/A'}</strong><br><br>"
            f"\"{safe_preview or 'No text returned.'}\""
        )
        return render_stream_card("⚖️ Judge", body, node_name, escape_body=False)

    if node_name == "fact_checker":
        approved = updates.get("is_fact_approved", False)
        status_icon = "✅ PASS" if approved else "❌ FAIL"
        feedback = updates.get("fact_checker_feedback", "") if approved else None
        
        rationale = updates.get("fact_checker_rationale", "")
        safe_rationale = html.escape(rationale).replace('\n', '<br>')

        body = (
            f"<details style='margin-bottom: 0.5rem; cursor: pointer;'>"
            f"  <summary style='font-weight: 600; outline: none;'>💬 Rationale</summary>"
            f"  <div style='margin-top: 0.5rem; padding: 0.8rem; background-color: rgba(0,0,0,0.05); border-radius: 0.4rem; font-size: 0.95em;'>"
            f"      {safe_rationale}"
            f"  </div>"
            f"</details>"
            f"<strong>Verdict: {status_icon}</strong>"
        )

        if feedback:
            safe_feedback = html.escape(feedback).replace('\n', '<br>')
            body += (
                f"\n\n📢 Feedback: {safe_feedback}"
            )
        return render_stream_card("🔎 Fact Checker", body, node_name, escape_body=False)

    if node_name == "readability_evaluator":
        approved = updates.get("is_readability_approved", False)
        status_icon = "✅ PASS" if approved else "❌ FAIL"
        metrics = updates.get("current_metrics", {})
        feedback = updates.get("readability_evaluator_feedback", "") if not approved else None
        reference_text = updates.get("reference_text", "")
        
        body = f"Verdict: {status_icon}"
        
        # Solo mostrar métricas si reference_text fue proporcionado
        if reference_text != "":
            lines = []
            for metric, value in metrics.items():
                if isinstance(value, float):
                    lines.append(f"  ▪️ {metric}: {value:.2f}")
                else:
                    lines.append(f"  ▪️ {metric}: {value}")
            metrics_text = "\n".join(lines) or "  No metrics reported."
            body += f"\n\n📊 Metrics Details:\n{metrics_text}"
        
        if feedback:
            safe_feedback = html.escape(feedback).replace('\n', '<br>')
            body += f"\n\n📢 Feedback: {safe_feedback}"
        return render_stream_card("📏 Readability Evaluator", body, node_name)

    if node_name == "editor":
        corrected_text = updates.get("current_simplified_text", "")
        preview = corrected_text.replace("\n", " ")
            
        body = f"✨ Corrected text preview:\n\"{preview or 'No text returned.'}\""
        return render_stream_card("✏️ Editor", body, node_name)

    if node_name == "term_explainer":
        term_explanations = updates.get("term_explanations", {})
        body = f"🔍 Explanations prepared for {len(term_explanations)} term(s):\n\n"
        
        # Formato de etiquetas y explicaciones para los términos
        if term_explanations:
            for term, info in sorted(term_explanations.items()):
                dictionary_term = info.get("dictionary_term", term)
                explanation = info.get("explanation", "No explanation provided.")
                
                body += f"  🏷️ {dictionary_term.upper()}\n  \"{explanation}\"\n\n"
        else:
            body += "  No terms found."
            
        return render_stream_card("📚 Term Explainer", body, node_name)

    if node_name == "auditors":
        fact_ok = final_state.get("is_fact_approved", False)
        read_ok = final_state.get("is_readability_approved", False)
        # Obtenemos la iteración actual para saber si hemos llegado al límite (asumimos 3 como máximo)
        iteration_count = final_state.get("iteration_count", 0)
        
        fact_icon = "✅ PASS" if fact_ok else "❌ FAIL"
        read_icon = "✅ PASS" if read_ok else "❌ FAIL"
        
        is_approved = fact_ok and read_ok
        
        # Ajustamos el mensaje a la lógica real del grafo
        if is_approved:
            final_icon = "🎉 APPROVED - Sending the approved version to Term Explainer"
        elif iteration_count >= 3:
            final_icon = "⚠️ REJECTED - ⏭️ MAX ITERATIONS REACHED. Sending last simplified version to Term Explainer."
        else:
            final_icon = "⚠️ REJECTED - Sending to Editor for revision"
        
        body = f"Final Assessment (Iteration {iteration_count}):\n  ▪️ Fact Checker: {fact_icon}\n  ▪️ Readability Evaluator: {read_icon}\n\nResult: {final_icon}"
        return render_stream_card("📋 Auditor Aggregator", body, node_name)

    return render_stream_card(humanize_node_name(node_name), str(updates), node_name)


async def run_graph_execution(app, complex_text: str, reference_text: str) -> Dict[str, Any]:
    initial_state: Dict[str, Any] = {
        "complex_text": complex_text,
        "reference_text": reference_text,
        "drafts": {},
        "is_input_in_scope": True,
        "guardrail_triggered": False,
        "guardrail_rationale": "",
        "guardrail_message": "",
        "selected_draft_letter": "",
        "current_simplified_text": "",
        "current_metrics": {},
        "iteration_count": 0,
        "is_fact_approved": False,
        "is_readability_approved": False,
        "is_approved": False,
        "term_explanations": {},
    }

    final_state = dict(initial_state)
    stream_entries = []
    execution_log = []

    hood_log = st.empty()

    async for output in app.astream(initial_state, stream_mode="updates"):
        for node_name, updates in output.items():
            for key, value in updates.items():
                final_state[key] = value

            card_html = format_update_card(node_name, updates, final_state)
            stream_entries.append(card_html)
            execution_log.append({"node": node_name, "updates": updates, "html": card_html})
            
            hood_log.markdown("".join(stream_entries), unsafe_allow_html=True)
    
    # Store execution log in final state for later display
    final_state["_execution_log"] = execution_log
    
    return final_state


def main() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown("# ⚕️ Medical Plain Language Simplifier")

    # Initialize session state
    if "final_state" not in st.session_state:
        st.session_state.final_state = None

    if "input_text" not in st.session_state:
        st.session_state.input_text = ""

    if "reference_text" not in st.session_state:
        st.session_state.reference_text = ""

    if "show_results" not in st.session_state:
        st.session_state.show_results = False

    if "carousel_index" not in st.session_state:
        st.session_state.carousel_index = 0

    # Reset to initial screen
    if st.session_state.show_results:
        if st.button("Simplify another medical abstract", type="primary"):
            st.session_state.show_results = False
            st.session_state.final_state = None
            st.session_state.input_text = ""
            st.session_state.reference_text = ""
            st.rerun()

        st.divider()

        # Display results layout: original and simplified side by side
        columns = st.columns(2)
        with columns[0]:
            render_text_panel(
                "Original Text",
                safe_text_block(st.session_state.input_text),
                original=True,
            )

        with columns[1]:
            simplified_text = st.session_state.final_state.get("current_simplified_text", "")
            term_explanations = st.session_state.final_state.get("term_explanations", {})
            if simplified_text:
                rendered_text = apply_tooltips(simplified_text, term_explanations)
            else:
                rendered_text = "<div class='muted-note'>No simplified text was returned by the workflow.</div>"
            render_text_panel("Simplified Text", rendered_text)

        st.divider()

        # Display agents' reasoning process (sin desplegable ni texto extra)
        st.markdown("<div class='section-title'>Agents' reasoning process</div>", unsafe_allow_html=True)
        _display_execution_summary(st.session_state.final_state)

    else:
        # Initial screen: input form
        with st.form("simplifier_form", clear_on_submit=False):
            user_text = st.text_area(
                "Medical abstract to simplify:",
                value=st.session_state.input_text,
                height=220,
                placeholder="Write your medical abstract here.",
            )
            
            submitted = st.form_submit_button("Simplify")
        
        examples_placeholder = st.empty()

        # 2. METEMOS TODOS LOS EJEMPLOS DENTRO DE LA CAJA
        with examples_placeholder.container():
            st.markdown("### Example Texts")
            st.markdown("Navigate through examples and select one to try:")
            
            examples = load_examples()
            if examples:
                examples_per_view = 3  # Show 3 examples at a time
                total_examples = len(examples)
                max_index = max(0, total_examples - examples_per_view)
                
                # Display carousel items
                carousel_items = examples[st.session_state.carousel_index:st.session_state.carousel_index + examples_per_view]
                cols = st.columns(len(carousel_items))
                
                for col_idx, example in enumerate(carousel_items):
                    with cols[col_idx]:
                        with st.container(border=True):
                            # Título
                            st.markdown(f"<div style='font-size: 1.15rem; font-weight: 700; margin-bottom: 10px;'> Abstract: {html.escape(example['pair_id'])}</div>", unsafe_allow_html=True)
                            
                            # Texto con scroll
                            st.markdown(
                                f"<div style='height: 200px; overflow-y: auto; font-size: 1rem; "
                                f"margin-bottom: 20px; padding-right: 8px; line-height: 1.6; color: #31333F;'>"
                                f"{html.escape(example['complex'])}"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                            
                            # Botón centrado
                            c1, c2, c3 = st.columns([1, 1.5, 1])
                            with c2:
                                if st.button("Use this example", key=f"example_{example['id']}", use_container_width=True):
                                    st.session_state.input_text = example["complex"]
                                    st.session_state.reference_text = example.get("simple", DEFAULT_REFERENCE_TEXT)
                                    st.session_state.show_results = False
                                    st.rerun()
                
                # Navigation row 
                nav_col1, spacer1, nav_col2, spacer2, nav_col3 = st.columns([0.75, 1.5, 4, 1.5, 0.75], vertical_alignment="center")
                
                with nav_col1:
                    if st.button("◀ Previous", key="prev_examples", use_container_width=True):
                        st.session_state.carousel_index = (st.session_state.carousel_index - 1) % (max_index + 1)
                        st.rerun()
                
                with nav_col2:
                    current_start = st.session_state.carousel_index + 1
                    current_end = min(st.session_state.carousel_index + examples_per_view, total_examples)
                    st.markdown(
                        f"<p style='text-align: center; color: #888; margin-top: 0.4rem;'>Showing {current_start}-{current_end} of {total_examples}</p>",
                        unsafe_allow_html=True
                    )
                    
                with nav_col3:
                    if st.button("Next ▶", key="next_examples", use_container_width=True):
                        st.session_state.carousel_index = (st.session_state.carousel_index + 1) % (max_index + 1)
                        st.rerun()
            else:
                st.info("No examples available from the dataset.")
        if submitted:
            user_text_stripped = user_text.strip()
            if not user_text_stripped:
                st.error("Please enter some text before running the simplifier.")
                return

            st.session_state.input_text = user_text_stripped

            # If no reference was selected (manual input), set it to empty.
            # If an example was selected, keep the example's reference_text.
            reference_text = st.session_state.reference_text

            examples_placeholder.empty()
            try:
                graph = get_graph()
                loading_placeholder = st.empty()
                
                # 1. Cargamos tu robot.png local
                img_path = os.path.join(os.path.dirname(__file__), "robot.png")
                try:
                    img_base64 = get_local_img_as_base64(img_path)
                    img_src = f"data:image/png;base64,{img_base64}"
                except Exception:
                    img_src = "" 

                # 2. Usamos componentes de Streamlit para renderizar el loader
                with loading_placeholder.container():
                    components.html(
                        f"""
                        <style>
                            .container {{
                                display: flex;
                                flex-direction: column;
                                align-items: center;
                                justify-content: center;
                                height: 100%;
                                font-family: 'Source Sans Pro', sans-serif;
                            }}
                            .text {{
                                margin-top: 12px;
                                font-weight: 600;
                                color: #454632;
                                font-size: 1rem;
                            }}
                        </style>
                        <div class="container">
                            <script type="module" src="https://cdn.jsdelivr.net/npm/ldrs/dist/auto/trio.js"></script>
                            
                            <l-trio size="55" speed="1.3" color="#454632"></l-trio>
                            
                            <img src="{img_src}" style="width: 70px; height: auto; margin-top: 15px;">
                            
                            <div class="text">Simplifying medical abstract ...</div>
                        </div>
                        """,
                        height=250, # Reducido ligeramente para evitar espacios vacíos
                    )

                # 3. Ejecución del grafo
                final_state = asyncio.run(
                    run_graph_execution(
                        graph,
                        st.session_state.input_text,
                        reference_text,
                    )
                )

                # 4. Limpieza y chequeo del guardaraíl
                loading_placeholder.empty()

                # Si el guardaraíl fue activado, mostrar mensaje de rechazo y volver a mostrar ejemplos
                if final_state.get("guardrail_triggered", False):
                    st.error(
                        f"❌ **Input out of scope**\n\n{final_state.get('guardrail_message', 'Please provide a medical or biomedical text.')}"
                    )
                    st.divider()
                    
                    # Recrear la sección de ejemplos
                    st.markdown("### Example Texts")
                    st.markdown("Navigate through examples and select one to try:")
                    
                    examples = load_examples()
                    if examples:
                        examples_per_view = 3
                        total_examples = len(examples)
                        max_index = max(0, total_examples - examples_per_view)
                        
                        carousel_items = examples[st.session_state.carousel_index:st.session_state.carousel_index + examples_per_view]
                        cols = st.columns(len(carousel_items))
                        
                        for col_idx, example in enumerate(carousel_items):
                            with cols[col_idx]:
                                with st.container(border=True):
                                    st.markdown(f"<div style='font-size: 1.15rem; font-weight: 700; margin-bottom: 10px;'> Abstract: {html.escape(example['pair_id'])}</div>", unsafe_allow_html=True)
                                    
                                    st.markdown(
                                        f"<div style='height: 200px; overflow-y: auto; font-size: 1rem; "
                                        f"margin-bottom: 20px; padding-right: 8px; line-height: 1.6; color: #31333F;'>"
                                        f"{html.escape(example['complex'])}"
                                        f"</div>",
                                        unsafe_allow_html=True
                                    )
                                    
                                    c1, c2, c3 = st.columns([1, 1.5, 1])
                                    with c2:
                                        if st.button("Use this example", key=f"example_retry_{example['id']}", use_container_width=True):
                                            st.session_state.input_text = example["complex"]
                                            st.session_state.reference_text = example.get("simple", DEFAULT_REFERENCE_TEXT)
                                            st.rerun()
                        
                        nav_col1, spacer1, nav_col2, spacer2, nav_col3 = st.columns([0.75, 1.5, 4, 1.5, 0.75], vertical_alignment="center")
                        
                        with nav_col1:
                            if st.button("◀ Previous", key="prev_examples_retry", use_container_width=True):
                                st.session_state.carousel_index = (st.session_state.carousel_index - 1) % (max_index + 1)
                                st.rerun()
                        
                        with nav_col2:
                            current_start = st.session_state.carousel_index + 1
                            current_end = min(st.session_state.carousel_index + examples_per_view, total_examples)
                            st.markdown(
                                f"<p style='text-align: center; color: #888; margin-top: 0.4rem;'>Showing {current_start}-{current_end} of {total_examples}</p>",
                                unsafe_allow_html=True
                            )
                            
                        with nav_col3:
                            if st.button("Next ▶", key="next_examples_retry", use_container_width=True):
                                st.session_state.carousel_index = (st.session_state.carousel_index + 1) % (max_index + 1)
                                st.rerun()
                else:
                    # El guardaraíl pasó, mostrar resultados
                    st.session_state.final_state = final_state
                    st.session_state.show_results = True
                    st.rerun()

            except Exception as exc:
                st.error(f"The workflow could not be executed: {exc}")
                return


def _display_execution_summary(final_state: Dict[str, Any]) -> None:
    """Display a summary of the workflow execution."""
    
    execution_log = final_state.get("_execution_log", [])
    if execution_log:
        # Envolvemos todas las tarjetas en nuestro contenedor de timeline
        html_content = "<div class='timeline-wrapper'>"
        for log_entry in execution_log:
            html_content += log_entry["html"]
        html_content += "</div>"
        
        st.markdown(html_content, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
