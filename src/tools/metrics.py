import evaluate
import numpy as np
from langchain_core.tools import StructuredTool

class MetricsEvaluator:

    def __init__(self):
        print("Loading evaluation metrics: SARI, BLEU and BERTScore F1.")
        self.sari_metric = evaluate.load("sari")
        self.bleu_metric = evaluate.load("bleu")
        self.bertscore_metric = evaluate.load("bertscore")
        print("Evluation metrics loaded.")

    def calc_simplification_metrics(self, complex_text: str, current_simplified_text: str, reference_text: str) -> dict:
        """
        Calculates SARI, BLEU y BERTScore_F1 metrics to evaluate the current simplified text.
        Receives the original text, the current simplified text given by the Plain Language Simplifier agent
        and the reference text.
        """

        sources = [complex_text]
        predictions = [current_simplified_text]
        references = [[reference_text]]

        try:
            sari_score = self.sari_metric.compute(
                sources=sources,
                predictions=predictions,
                references=references
            )
        except Exception as e:
            print(f"Error calculating SARI: {e}")


        try:
            bleu_score = self.bleu_metric.compute(
                predictions=predictions,
                references=references
            )
        except Exception as e:
            print(f"Error calculating BLEU: {e}")


        try:
            bert_score = self.bertscore_metric.compute(
                predictions=predictions,
                references=references,
                lang="en"
            )
        except Exception as e:
            print(f"Error calculating BERTScore: {e}")

        return {
            "SARI": sari_score['sari'],
            "BLEU": bleu_score['bleu'],
            "BERTScore_F1": bert_score['f1'][0]
        }
    
evaluator = MetricsEvaluator()

calc_metrics_tool = StructuredTool.from_function(
    func=evaluator.calc_simplification_metrics,
    name="calc_simplification_metrics",
    description="Calculates SARI, BLEU y BERTScore_F1 metrics to evaluate the current simplified text. Receives the original text, the current simplified text given by the Plain Language Simplifier agent and the reference text."
)