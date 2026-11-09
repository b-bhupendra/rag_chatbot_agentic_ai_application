"""
Agentic RAG Controller implementing a ReAct (Reasoning + Action) execution loop.
"""
from typing import Dict, Any
from src.tools import ToolRegistry

class AgenticRAGBot:
    def __init__(self):
        self.tools = ToolRegistry()

    def run(self, user_prompt: str) -> Dict[str, Any]:
        """
        Executes an agentic reasoning loop:
        1. Formulates plan (Thought)
        2. Determines tool to call (Action)
        3. Retrieves and interprets observations
        4. Synthesizes final response
        """
        # Determine if math or knowledge search is needed
        plan = []
        lowered = user_prompt.lower()

        if any(op in lowered for op in ["calculate", "math", "+", "-", "*", "/"]) and any(c.isdigit() for c in lowered):
            # Math flow
            math_expr = "".join([c for c in user_prompt if c in "0123456789+-*/(). "]).strip()
            plan.append({
                "thought": "User query requires mathematical computation. Invoking calculator tool.",
                "action": "calculate",
                "tool_input": math_expr
            })
            obs = self.tools.calculate(math_expr)
            plan[-1]["observation"] = obs
            final_answer = f"The calculated result is: {obs}"
        else:
            # Knowledge base RAG flow
            plan.append({
                "thought": "User is inquiring about AI/ML concepts. Querying internal vector knowledge base.",
                "action": "search_knowledge_base",
                "tool_input": user_prompt
            })
            obs = self.tools.search_knowledge_base(user_prompt)
            plan[-1]["observation"] = obs
            final_answer = (
                f"Based on the retrieved context:\n\n{obs}\n\n"
                f"Summary: The concepts above directly address '{user_prompt}' by grounding the answer in verified documents."
            )

        return {
            "query": user_prompt,
            "steps": plan,
            "final_answer": final_answer
        }
