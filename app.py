import asyncio
import html
import re
import os
from typing import Any, Dict

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

    .stream-card {
        border-left: 4px solid var(--primary-color, #0b6efd);
        border-radius: 0.6rem;
        padding: 0.85rem 1rem;
        margin-bottom: 0.65rem;
        border: 1px solid rgba(128, 128, 128, 0.16);
        background: #ADAF7E;
        color: #31333F;
        border-left-width: 8px;
        border-left-style: solid;
    }

    .stream-card h4 {
        margin: 0 0 0.25rem 0;
        font-size: 1rem;
    }

    .stream-card p {
        margin: 0.2rem 0 0 0;
        white-space: pre-wrap;
    }

    /* --- COLORES ESPECÍFICOS POR AGENTE --- */
    .card-parallel-drafters { 
        background-color: #5B9ECF80; 
        border-left-color: #5B9ECF; 
    }
    .card-fact-checker { 
        background-color: #C8AA1080; 
        border-left-color: #C8AA10; 
    }
    .card-judge { 
        background-color: #7F67A180; 
        border-left-color: #7F67A1; 
    }
    .card-readability-evaluator { 
        background-color: #BF870E80; 
        border-left-color: #BF870E; 
    }
    .card-term-explainer { 
        background-color: #70965D80; 
        border-left-color: #70965D; 
    }
    .card-editor { 
        background-color: #A9452B80; 
        border-left-color: #A9452B; 
    }

    /* Para los auditores y nodos no mapeados */
    .card-auditors { 
        background-color: #4A556880; 
        border-left-color: #4A5568; 
    } 
    .card-default { 
        background-color: #71809680; 
        border-left-color: #718096; 
    }


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


DEFAULT_COMPLEX_TEXT = """Ten prospective, parallel-group design, randomised controlled trials, involving a total of 577 participants with type 1 and type 2 diabetes mellitus, were identified. Risk of bias was high or unclear in all but two trials, which were assessed as having moderate risk of bias. Risk of bias in some domains was high in 50% of trials. Oral monopreparations of cinnamon (predominantly Cinnamomum cassia) were administered at a mean dose of 2 g daily, for a period ranging from 4 to 16 weeks. The effect of cinnamon on fasting blood glucose level was inconclusive. No statistically significant difference in glycosylated haemoglobin A1c (HbA1c), serum insulin or postprandial glucose was found between cinnamon and control groups. There were insufficient data to pool results for insulin sensitivity. No trials reported health-related quality of life, morbidity, mortality or costs. Adverse reactions to oral cinnamon were infrequent and generally mild in nature. There is insufficient evidence to support the use of cinnamon for type 1 or type 2 diabetes mellitus. Further trials, which address the issues of allocation concealment and blinding, are now required. The inclusion of other important endpoints, such as health-related quality of life, diabetes complications and costs, is also needed."""


DEFAULT_REFERENCE_TEXT = """The authors identified 10 randomised controlled trials, which involved 577 participants with diabetes mellitus. Cinnamon was administered in tablet or capsule form, at a mean dose of 2 g daily, for four to 16 weeks. Cinnamon bark has been shown in a number of animal studies to improve blood sugar levels, though its effect in humans is not too clear. Hence, the review authors set out to determine the effect of oral cinnamon extract on blood sugar and other outcomes. The review authors found cinnamon to be no more effective than placebo, another active medication or no treatment in reducing glucose levels and glycosylated haemoglobin A1c (HbA1c), a long-term measurement of glucose control. None of the trials looked at health-related quality of life, morbidity, death from any cause or costs. Adverse reactions to cinnamon treatment were generally mild and infrequent. Further trials investigating long-term benefits and risks of the use of cinnamon for diabetes mellitus are required. Rigorous study design, quality reporting of study methods, and consideration of important outcomes such as health-related quality of life and diabetes complications, are key areas in need of attention."""


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
        "parallel_drafters": "Drafting Panel",
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



def render_stream_card(title: str, body: str, node_id: str = "default") -> str:
    css_class = f"stream-card card-{node_id.replace('_', '-')}"
    formatted_body = html.escape(body).replace('\n', '<br>')
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
    if node_name == "parallel_drafters":
        drafts = updates.get("drafts", {})
        draft_lines = []
        for letter in ["A", "B", "C", "D"]:
            draft_text = drafts.get(letter, "")
            preview = draft_text.replace("\n", " ")[:180]
            if draft_text and len(draft_text) > 180:
                preview += "..."
            draft_lines.append(f"{letter}: {preview or 'No draft returned.'}")
        body = "Drafts generated.\n" + "\n".join(draft_lines)
        return render_stream_card("Drafting Panel", body, node_name)

    if node_name == "judge":
        selected_letter = updates.get("selected_draft_letter", "")
        selected_text = updates.get("current_simplified_text", "")
        preview = selected_text.replace("\n", " ")[:260]
        if selected_text and len(selected_text) > 260:
            preview += "..."
        body = f"Selected draft: {selected_letter or 'N/A'}\nPreview: {preview or 'No text returned.'}"
        return render_stream_card("Judge", body, node_name)

    if node_name == "fact_checker":
        approved = updates.get("is_fact_approved", False)
        feedback = final_state.get("feedback_history", [])
        latest_feedback = feedback[-1] if feedback else "No factual issues detected."
        body = f"Verdict: {'Approved' if approved else 'Rejected'}\n{latest_feedback}"
        return render_stream_card("Fact Checker", body, node_name)

    if node_name == "readability_evaluator":
        approved = updates.get("is_readability_approved", False)
        metrics = updates.get("current_metrics", {})
        body = (
            f"Verdict: {'Approved' if approved else 'Rejected'}\n"
            f"Metrics:\n{format_metrics(metrics)}" # Asumo que format_metrics está definida en otra parte
        )
        return render_stream_card("Readability Evaluator", body, node_name)

    if node_name == "editor":
        iteration_count = updates.get("iteration_count", final_state.get("iteration_count", 0))
        corrected_text = updates.get("current_simplified_text", "")
        preview = corrected_text.replace("\n", " ")[:260]
        if corrected_text and len(corrected_text) > 260:
            preview += "..."
        body = f"Iteration: {iteration_count}\nCorrected text preview: {preview or 'No text returned.'}"
        return render_stream_card("Editor", body, node_name)

    if node_name == "term_explainer":
        term_explanations = updates.get("term_explanations", {})
        terms = ", ".join(sorted(term_explanations.keys())) or "No terms found."
        body = f"Explanations prepared for {len(term_explanations)} term(s).\n{terms}"
        return render_stream_card("Term Explainer", body, node_name)

    if node_name == "auditors":
        fact_ok = final_state.get("is_fact_approved", False)
        read_ok = final_state.get("is_readability_approved", False)
        body = f"Fact Checker: {fact_ok}\nReadability Evaluator: {read_ok}\nApproved: {fact_ok and read_ok}"
        return render_stream_card("Auditor Aggregator", body, node_name)

    return render_stream_card(humanize_node_name(node_name), str(updates), node_name)


async def run_graph_execution(app, complex_text: str, reference_text: str) -> Dict[str, Any]:
    initial_state: Dict[str, Any] = {
        "complex_text": complex_text,
        "reference_text": reference_text,
        "drafts": {},
        "selected_draft_letter": "",
        "current_simplified_text": "",
        "current_metrics": {},
        "feedback_history": [],
        "iteration_count": 0,
        "is_fact_approved": False,
        "is_readability_approved": False,
        "is_approved": False,
        "term_explanations": {},
    }

    final_state = dict(initial_state)
    stream_entries = []
    execution_log = []

    hood_status = st.empty()
    hood_log = st.empty()

    hood_status.info("Starting LangGraph execution...")
    hood_log.markdown(
        "<div class='muted-note'>Live node updates will appear here as the workflow runs.</div>",
        unsafe_allow_html=True,
    )

    async for output in app.astream(initial_state, stream_mode="updates"):
        for node_name, updates in output.items():
            for key, value in updates.items():
                if key == "feedback_history":
                    final_state.setdefault("feedback_history", [])
                    final_state["feedback_history"].extend(value)
                else:
                    final_state[key] = value

            card_html = format_update_card(node_name, updates, final_state)
            stream_entries.append(card_html)
            execution_log.append({"node": node_name, "updates": updates, "html": card_html})
            
            hood_log.markdown("".join(stream_entries), unsafe_allow_html=True)
            hood_status.info(f"Latest node finished: {humanize_node_name(node_name)}")

    hood_status.success("LangGraph execution completed.")
    
    # Store execution log in final state for later display
    final_state["_execution_log"] = execution_log
    
    return final_state


def main() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown("# Medical Plain Language Simplifier")

    # Initialize session state
    if "final_state" not in st.session_state:
        st.session_state.final_state = None

    if "input_text" not in st.session_state:
        st.session_state.input_text = DEFAULT_COMPLEX_TEXT

    if "show_results" not in st.session_state:
        st.session_state.show_results = False

    if "carousel_index" not in st.session_state:
        st.session_state.carousel_index = 0

    # Reset to initial screen
    if st.session_state.show_results:
        if st.button("Simplify another medical abstract", type="primary"):
            st.session_state.show_results = False
            st.session_state.final_state = None
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

        # Display agents' reasoning process
        with st.expander("Agents' reasoning process", expanded=True):
            st.markdown(
                "<div class='muted-note'>The workflow execution has completed. Below is a summary of the agents' decisions.</div>",
                unsafe_allow_html=True,
            )
            # Recreate the execution flow display from the final state
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
            examples_placeholder.empty()
            user_text_stripped = user_text.strip()
            if not user_text_stripped:
                st.error("Please enter some text before running the simplifier.")
                return

            st.session_state.input_text = user_text_stripped

            try:
                graph = get_graph()

                # Show placeholder for results
                st.info("Processing your text... Please wait while the agents work.")

                # Run the graph and collect execution trace
                final_state = asyncio.run(
                    run_graph_execution(
                        graph,
                        st.session_state.input_text,
                        DEFAULT_REFERENCE_TEXT,
                    )
                )

                st.session_state.final_state = final_state
                st.session_state.show_results = True
                st.rerun()

            except Exception as exc:
                st.error(f"The workflow could not be executed: {exc}")
                return


def _display_execution_summary(final_state: Dict[str, Any]) -> None:
    """Display a summary of the workflow execution."""
    
    # Display execution log if available
    execution_log = final_state.get("_execution_log", [])
    if execution_log:
        st.markdown("**Step-by-step agent execution:**")
        for idx, log_entry in enumerate(execution_log, 1):
            node_name = log_entry["node"]
            html_card = log_entry["html"]
            with st.expander(f"Step {idx}: {humanize_node_name(node_name)}", expanded=False):
                st.markdown(html_card, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
