from fastmcp import FastMCP
from src.tools.metrics import MetricsEvaluator

evaluator = MetricsEvaluator()

mcp = FastMCP("metrics_server", version ="1.0.0")

@mcp.tool()
def calculate_metrics(
    complex_text: str,
    current_simplified_text: str,
    reference_text: str,
) -> dict:
    """Return simplification quality and readability metrics for a simplified text."""

    return evaluator.calc_simplification_metrics(
        complex_text=complex_text,
        current_simplified_text=current_simplified_text,
        reference_text=reference_text
    )

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8020)