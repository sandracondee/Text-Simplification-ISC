import json
import difflib
from fastmcp import FastMCP

medical_dict = {}

try:
    with open("data/medical_dictionary.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        definitions_list = raw_data.get("definitions", [])
        
        for item in definitions_list:
            term_string = item.get("term", "")
            definition_text = item.get("definition", "")
            
            if not term_string or not definition_text:
                continue
                
            terms = str(term_string).split(",")
            
            for t in terms:
                clean_term = t.strip().lower()
                if clean_term:
                    medical_dict[clean_term] = str(definition_text)

except FileNotFoundError:
    print("Could not find 'pl_medical_dictionary/pl_medical_dictionary.json'. Please ensure the file exists and is in the correct location.")

mcp = FastMCP("search_server", version="1.0.0")

@mcp.tool()
def lookup_medical_term(term: str) -> str:
    """
    Looks up a complex medical term in the local PL medical dictionary.
    Returns the plain-language explanation of the term.
    """
    term_lower = term.lower().strip()

    # Exact match
    if term_lower in medical_dict:
        return medical_dict[term_lower]

    # Fuzzy match 80% similarity
    possible_matches = difflib.get_close_matches(term_lower, medical_dict.keys(), n=1, cutoff=0.8)
    
    if possible_matches:
        best_match = possible_matches[0]
        explanation = medical_dict[best_match]
        return f"Found as '{best_match}': {explanation}"

    return "Term not found in the dictionary."

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8021)