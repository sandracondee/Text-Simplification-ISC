import asyncio
import os
from dotenv import load_dotenv
from src.graph.workflow import build_graph

load_dotenv()

async def main():
    print("==="*25)
    print("Initializing Simplification Multi-Agent System")
    print("==="*25 + "\n")
    
    app = build_graph()
    
    sample_complex_text = """Ten prospective, parallel-group design, randomised controlled trials, involving a total of 577 participants with type 1 and type 2 diabetes mellitus, were identified. Risk of bias was high or unclear in all but two trials, which were assessed as having moderate risk of bias. Risk of bias in some domains was high in 50% of trials. Oral monopreparations of cinnamon (predominantly Cinnamomum cassia) were administered at a mean dose of 2 g daily, for a period ranging from 4 to 16 weeks. The effect of cinnamon on fasting blood glucose level was inconclusive. No statistically significant difference in glycosylated haemoglobin A1c (HbA1c), serum insulin or postprandial glucose was found between cinnamon and control groups. There were insufficient data to pool results for insulin sensitivity. No trials reported health-related quality of life, morbidity, mortality or costs. Adverse reactions to oral cinnamon were infrequent and generally mild in nature. There is insufficient evidence to support the use of cinnamon for type 1 or type 2 diabetes mellitus. Further trials, which address the issues of allocation concealment and blinding, are now required. The inclusion of other important endpoints, such as health-related quality of life, diabetes complications and costs, is also needed.
    """
    
    sample_reference_text = "The authors identified 10 randomised controlled trials, which involved 577 participants with diabetes mellitus. Cinnamon was administered in tablet or capsule form, at a mean dose of 2 g daily, for four to 16 weeks. Cinnamon bark has been shown in a number of animal studies to improve blood sugar levels, though its effect in humans is not too clear. Hence, the review authors set out to determine the effect of oral cinnamon extract on blood sugar and other outcomes. The review authors found cinnamon to be no more effective than placebo, another active medication or no treatment in reducing glucose levels and glycosylated haemoglobin A1c (HbA1c), a long-term measurement of glucose control. None of the trials looked at health-related quality of life, morbidity, death from any cause or costs. Adverse reactions to cinnamon treatment were generally mild and infrequent. Further trials investigating long-term benefits and risks of the use of cinnamon for diabetes mellitus are required. Rigorous study design, quality reporting of study methods, and consideration of important outcomes such as health-related quality of life and diabetes complications, are key areas in need of attention."
    
    initial_state = {
        "complex_text": sample_complex_text,
        "reference_text": sample_reference_text,
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
        "is_approved": False 
    }
    
    final_output_updates = {}
    async for output in app.astream(initial_state):
        for node_name, updates in output.items():
            final_output_updates = updates
            
            # PARALLEL DRAFTERS OUTPUT
            if node_name == "parallel_drafters":
                drafts = updates.get("drafts", {})
                print("-> Drafts generated: A, B, C, D")
                for letter in ["A", "B", "C", "D"]:
                    text = drafts.get(letter, "")
                    preview = text.replace("\n", " ")[:180]
                    print(f"   {letter}: {preview}{'...' if len(text) > 180 else ''}")

            # JUDGE OUTPUT
            elif node_name == "judge":
                selected_letter = updates.get("selected_draft_letter", "")
                selected_text = updates.get("current_simplified_text", "")
                print(f"-> Judge selected draft: {selected_letter}")
                print(f"-> Selected draft text:\n{selected_text}\n")

            # EDITOR OUTPUT
            elif node_name == "editor":
                iter_num = updates.get("iteration_count", 0)
                corrected = updates.get("current_simplified_text", "")
                print(f"-> Corrected draft (Iteration {iter_num}):\n{corrected}\n")
                
            # EVALUATORS OUTPUT (Verdict & Feedback)
            elif node_name in ["fact_checker", "readability_evaluator"]:
                approved = updates.get("is_fact_approved") if node_name == "fact_checker" else updates.get("is_readability_approved")
                status_icon = "✅ APPROVED" if approved else "❌ REJECTED"
                print(f"{node_name} -> Verdict: {status_icon}")

                if node_name == "readability_evaluator":
                    metrics = updates.get("current_metrics")
                    print(metrics)
                
                feedback_key = "fact_checker_feedback" if node_name == "fact_checker" else "readability_evaluator_feedback"
                feedback_text = updates.get(feedback_key, "")
                if feedback_text:
                    print(f"-> Critique sent to Simplifier:\n{feedback_text}\n")

    print("\n" + "==="*25)
    print("WORKFLOW FINISHED")
    print("==="*25 + "\n")
    
    final_state = updates 
    if not final_state: 
        final_state = final_output_updates
        
    print("\n[ FINAL PLAIN LANGUAGE SUMMARY ]")
    print(final_state.get("current_simplified_text", "Failed to generate text."))
    
    print("\n[ FINAL EVALUATION METRICS ]")
    metrics = final_state.get("current_metrics", {})
    if metrics:
        for metric, value in metrics.items():
            formatted_value = f"{value:.2f}" if isinstance(value, float) else value
            print(f"- {metric}: {formatted_value}")
    else:
        print("- No metrics were reported.")

    print("\n[ EXPLANATIONS FOR KEY TERMS ]")
    term_explanations = final_state.get("term_explanations", {})
    if term_explanations:
        for term, explanations in term_explanations.items():
            print(f"\n- {term}:")
            for role, explanation in explanations.items():
                print(f"  {role}: {explanation}")
    else:
        print("- No term explanations were provided.")

    if final_state.get("guardrail_triggered"):
        print("\n🛡️ GUARDRAIL ACTIVATED: The input was outside the scope of the medical simplification system.")
        message = final_state.get("guardrail_message", "")
        if message:
            print(f"-> {message}")
    elif not final_state.get("is_approved"):
        print("\n⚠️ WARNING: The system reached the maximum iteration limit (3) without achieving full approval from the evaluators. Human review is recommended.")
    else:
        print("\n✅ SUCCESS: The text was fully approved by both the Fact-Checker and Readability Evaluator.")

if __name__ == "__main__":
    local_mode = os.getenv("LOCAL_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
    llm_provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    using_ollama = llm_provider == "ollama" or (not llm_provider and local_mode)

    if not using_ollama and not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError(
            "GOOGLE_API_KEY is missing. Add it to your .env file or use LOCAL_MODE=1/LLM_PROVIDER=ollama for local execution."
        )
        
    asyncio.run(main())