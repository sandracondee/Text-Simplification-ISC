import os
from dotenv import load_dotenv
from src.graph.workflow import build_graph

load_dotenv()

def main():
    print("==="*50)
    print("Initializing Simplification Multi-Agent System")
    print("==="*50 + "\n")
    
    app = build_graph()
    
    sample_complex_text = """
    Background: Acute otitis media (AOM) is one of the most common infectious diseases in children. 
    Objectives: To assess the efficacy of antibiotics for children with AOM. 
    Main results: We included 13 trials (3401 children). Antibiotics significantly reduced the number of children with pain at days 2 to 7 (RR 0.70, 95% CI 0.57 to 0.86; NNTB 16). 
    However, antibiotics caused adverse events such as vomiting, diarrhea, and rash (RR 1.38, 95% CI 1.19 to 1.59; NNTH 14).
    Authors' conclusions: Antibiotics have a small beneficial effect, but also cause side effects. Management should favor watchful waiting.
    """
    
    sample_reference_text = [
        "Ear infections are very common in children. This review looked at whether antibiotics help. We found that antibiotics slightly reduce ear pain after a few days. However, they also cause side effects like vomiting, diarrhea, and skin rashes. Because the benefits are small and the side effects are common, doctors should consider waiting a few days before giving antibiotics to see if the child gets better on their own."
    ]
    
    initial_state = {
        "complex_text": sample_complex_text,
        "reference_text": sample_reference_text,
        "core_information": "",
        "current_simplified_text": "",
        "current_metrics": {},
        "feedback_history": [],
        "iteration_count": 0,
        "is_approved": True 
    }
    
    final_output_updates = {}
    for output in app.stream(initial_state):
        for node_name, updates in output.items():
            final_output_updates = updates
            
            # ANALYST OUTPUT
            if node_name == "analyst":
                core_info = updates.get("core_information", "")
                print(f"-> Extracted Core Information:\n{core_info}\n")
                
            # SIMPLIFIER OUTPUT
            elif node_name == "simplifier":
                iter_num = updates.get('iteration_count', 1)
                draft = updates.get("current_simplified_text", "")
                print(f"-> Draft Generated (Iteration {iter_num}):\n{draft}\n")
                
            # EVALUATORS OUTPUT (Verdict & Feedback)
            elif node_name in ["fact_checker", "readability_evaluator"]:
                is_approved = updates.get("is_approved")
                status_icon = "✅ APPROVED" if is_approved else "❌ REJECTED"
                print(f"-> Verdict: {status_icon}")
                
                # If rejected, print the specific feedback it just generated
                if not is_approved:
                    feedback_list = updates.get("feedback_history", [])
                    if feedback_list:
                        # Print the last appended item in the history
                        print(f"-> Critique sent to Simplifier:\n{feedback_list[-1]}\n")

    print("\n" + "==="*50)
    print("WORKFLOW FINISHED")
    print("==="*50 + "\n")
    
    final_state = app.get_state({"configurable": {"thread_id": "1"}}).values 
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

    if not final_state.get("is_approved"):
        print("\n⚠️ WARNING: The system reached the maximum iteration limit (3) without achieving full approval from the evaluators. Human review is recommended.")
    else:
        print("\n✅ SUCCESS: The text was fully approved by both the Fact-Checker and Readability Evaluator.")

if __name__ == "__main__":
    if not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY is missing. Please add it to your .env file.")
        
    main()