"""
Tool definitions accessible to the Agent.
"""
from src.retriever import SimpleKnowledgeBase

class ToolRegistry:
    def __init__(self):
        self.kb = SimpleKnowledgeBase()

    def search_knowledge_base(self, query: str) -> str:
        """Searches internal documents and returns relevant context snippets."""
        results = self.kb.query(query)
        if not results:
            return "No matching documents found in knowledge base."
        output = []
        for i, doc in enumerate(results, start=1):
            output.append(f"[{i}] {doc['title']}: {doc['content']}")
        return "\n".join(output)

    def calculate(self, expression: str) -> str:
        """Safely evaluates basic arithmetic expressions."""
        try:
            # Simple whitelist evaluation
            allowed = set("0123456789+-*/(). ")
            if not all(c in allowed for c in expression):
                return "Error: Unsupported characters in calculation expression."
            return str(eval(expression, {"__builtins__": None}, {}))
        except Exception as e:
            return f"Error executing calculation: {str(e)}"
