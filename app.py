import asyncio
import html
import re
from typing import Any, Dict

import streamlit as st
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
    .app-shell {
        padding-top: 0.5rem;
    }

    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }

    .text-panel {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 0.8rem;
        padding: 1rem;
        line-height: 1.65;
        min-height: 100px;
        word-wrap: break-word;
    }

    /* Light mode text panel */
    @media (prefers-color-scheme: light) {
        .text-panel {
            background: #f5f5f5;
            color: #212529;
        }
    }

    /* Dark mode text panel */
    @media (prefers-color-scheme: dark) {
        .text-panel {
            background: #2c2f33;
            color: #e0e0e0;
        }
    }

    .text-panel.is-original {
        opacity: 0.98;
    }

    .tooltip {
        position: relative;
        display: inline;
        border-bottom: 1px dotted var(--primary-color, #0b6efd);
        cursor: help;
        font-weight: 600;
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
            background: #2c2f33;
            color: #e0e0e0;
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
            border-color: #2c2f33 transparent transparent transparent;
        }
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }

    .stream-card {
        border-left: 4px solid var(--primary-color, #0b6efd);
        border-radius: 0.6rem;
        padding: 0.85rem 1rem;
        margin-bottom: 0.65rem;
        border: 1px solid rgba(128, 128, 128, 0.16);
    }

    /* Light mode stream card */
    @media (prefers-color-scheme: light) {
        .stream-card {
            background: #f5f5f5;
            color: #212529;
        }
    }

    /* Dark mode stream card */
    @media (prefers-color-scheme: dark) {
        .stream-card {
            background: #2c2f33;
            color: #e0e0e0;
        }
    }

    .stream-card h4 {
        margin: 0 0 0.25rem 0;
        font-size: 1rem;
    }

    .stream-card p {
        margin: 0.2rem 0 0 0;
        white-space: pre-wrap;
    }

    .muted-note {
        opacity: 0.72;
        font-size: 0.95rem;
    }
</style>
"""


DEFAULT_COMPLEX_TEXT = """Ten prospective, parallel-group design, randomised controlled trials, involving a total of 577 participants with type 1 and type 2 diabetes mellitus, were identified. Risk of bias was high or unclear in all but two trials, which were assessed as having moderate risk of bias. Risk of bias in some domains was high in 50% of trials. Oral monopreparations of cinnamon (predominantly Cinnamomum cassia) were administered at a mean dose of 2 g daily, for a period ranging from 4 to 16 weeks. The effect of cinnamon on fasting blood glucose level was inconclusive. No statistically significant difference in glycosylated haemoglobin A1c (HbA1c), serum insulin or postprandial glucose was found between cinnamon and control groups. There were insufficient data to pool results for insulin sensitivity. No trials reported health-related quality of life, morbidity, mortality or costs. Adverse reactions to oral cinnamon were infrequent and generally mild in nature. There is insufficient evidence to support the use of cinnamon for type 1 or type 2 diabetes mellitus. Further trials, which address the issues of allocation concealment and blinding, are now required. The inclusion of other important endpoints, such as health-related quality of life, diabetes complications and costs, is also needed."""


DEFAULT_REFERENCE_TEXT = """The authors identified 10 randomised controlled trials, which involved 577 participants with diabetes mellitus. Cinnamon was administered in tablet or capsule form, at a mean dose of 2 g daily, for four to 16 weeks. Cinnamon bark has been shown in a number of animal studies to improve blood sugar levels, though its effect in humans is not too clear. Hence, the review authors set out to determine the effect of oral cinnamon extract on blood sugar and other outcomes. The review authors found cinnamon to be no more effective than placebo, another active medication or no treatment in reducing glucose levels and glycosylated haemoglobin A1c (HbA1c), a long-term measurement of glucose control. None of the trials looked at health-related quality of life, morbidity, death from any cause or costs. Adverse reactions to cinnamon treatment were generally mild and infrequent. Further trials investigating long-term benefits and risks of the use of cinnamon for diabetes mellitus are required. Rigorous study design, quality reporting of study methods, and consideration of important outcomes such as health-related quality of life and diabetes complications, are key areas in need of attention."""


def get_graph():
    """Build the compiled LangGraph once per Streamlit session."""
    return build_graph()


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


def render_stream_card(title: str, body: str) -> str:
    return (
        "<div class='stream-card'>"
        f"<h4>{html.escape(title)}</h4>"
        f"<p>{html.escape(body)}</p>"
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
        return render_stream_card("Drafting Panel", body)

    if node_name == "judge":
        selected_letter = updates.get("selected_draft_letter", "")
        selected_text = updates.get("current_simplified_text", "")
        preview = selected_text.replace("\n", " ")[:260]
        if selected_text and len(selected_text) > 260:
            preview += "..."
        body = f"Selected draft: {selected_letter or 'N/A'}\nPreview: {preview or 'No text returned.'}"
        return render_stream_card("Judge", body)

    if node_name == "fact_checker":
        approved = updates.get("is_fact_approved", False)
        feedback = final_state.get("feedback_history", [])
        latest_feedback = feedback[-1] if feedback else "No factual issues detected."
        body = f"Verdict: {'Approved' if approved else 'Rejected'}\n{latest_feedback}"
        return render_stream_card("Fact Checker", body)

    if node_name == "readability_evaluator":
        approved = updates.get("is_readability_approved", False)
        metrics = updates.get("current_metrics", {})
        body = (
            f"Verdict: {'Approved' if approved else 'Rejected'}\n"
            f"Metrics:\n{format_metrics(metrics)}"
        )
        return render_stream_card("Readability Evaluator", body)

    if node_name == "editor":
        iteration_count = updates.get("iteration_count", final_state.get("iteration_count", 0))
        corrected_text = updates.get("current_simplified_text", "")
        preview = corrected_text.replace("\n", " ")[:260]
        if corrected_text and len(corrected_text) > 260:
            preview += "..."
        body = f"Iteration: {iteration_count}\nCorrected text preview: {preview or 'No text returned.'}"
        return render_stream_card("Editor", body)

    if node_name == "term_explainer":
        term_explanations = updates.get("term_explanations", {})
        terms = ", ".join(sorted(term_explanations.keys())) or "No terms found."
        body = f"Explanations prepared for {len(term_explanations)} term(s).\n{terms}"
        return render_stream_card("Term Explainer", body)

    if node_name == "auditors":
        fact_ok = final_state.get("is_fact_approved", False)
        read_ok = final_state.get("is_readability_approved", False)
        body = f"Fact Checker: {fact_ok}\nReadability Evaluator: {read_ok}\nApproved: {fact_ok and read_ok}"
        return render_stream_card("Auditor Aggregator", body)

    return render_stream_card(humanize_node_name(node_name), str(updates))


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
    st.write(
        "Simplify complex medical text with a multi-agent LangGraph workflow and inspect the generated reasoning in real time."
    )

    # Initialize session state
    if "final_state" not in st.session_state:
        st.session_state.final_state = None

    if "input_text" not in st.session_state:
        st.session_state.input_text = DEFAULT_COMPLEX_TEXT

    if "show_results" not in st.session_state:
        st.session_state.show_results = False

    # Reset to initial screen
    if st.session_state.show_results:
        if st.button("Simplify another text", use_container_width=True):
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
                "Complex medical text",
                value=st.session_state.input_text,
                height=220,
                placeholder="Paste a medical abstract or clinical passage here...",
            )
            submitted = st.form_submit_button("Simplify", use_container_width=True)

        if submitted:
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
    
    st.divider()

    # Show final metrics
    current_metrics = final_state.get("current_metrics", {})
    if current_metrics:
        st.markdown("**Readability Metrics:**")
        metrics_text = format_metrics(current_metrics)
        st.markdown(f"```\n{metrics_text}\n```")

    # Show approval status
    is_fact_approved = final_state.get("is_fact_approved", False)
    is_readability_approved = final_state.get("is_readability_approved", False)

    st.markdown("**Final Approval Status:**")
    col1, col2 = st.columns(2)
    with col1:
        fact_status = "✅ Approved" if is_fact_approved else "❌ Rejected"
        st.markdown(f"**Fact Checker:** {fact_status}")
    with col2:
        read_status = "✅ Approved" if is_readability_approved else "❌ Rejected"
        st.markdown(f"**Readability Evaluator:** {read_status}")

    # Show term explanations
    term_explanations = final_state.get("term_explanations", {})
    if term_explanations:
        st.markdown("**Identified Complex Terms:**")
        for term, info in sorted(term_explanations.items()):
            with st.expander(f"📖 {term}"):
                st.markdown(f"**Dictionary Term:** {info.get('dictionary_term', term)}")
                st.markdown(f"**Explanation:** {info.get('explanation', 'N/A')}")


if __name__ == "__main__":
    main()
