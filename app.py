"""
Entrypoint for RAG Chatbot Agentic AI Application
Interactive CLI loop.
"""
from src.agent import AgenticRAGBot

def main():
    print("=" * 65)
    print(" 🤖 Welcome to the RAG Chatbot Agentic AI Application")
    print("=" * 65)
    print("Features:")
    print(" - Knowledge Retrieval Tool (Agentic RAG)")
    print(" - Computation / Calculator Tool")
    print(" - Step-by-Step Reason & Act (ReAct) inspection")
    print("-" * 65)
    print("Type your questions below, or type 'exit' / 'quit' to stop.\n")

    bot = AgenticRAGBot()

    # Pre-run sample demonstration
    sample_q = "Explain how RAG and Agentic AI work together"
    print(f">> Demo Query: '{sample_q}'")
    result = bot.run(sample_q)
    for step in result["steps"]:
        print(f"  [Thought]     : {step['thought']}")
        print(f"  [Action]      : {step['action']}({step['tool_input']})")
        print(f"  [Observation] : {step['observation']}")
    print(f"\n[Final Response]:\n{result['final_answer']}")
    print("=" * 65)

    while True:
        try:
            user_input = input("\nEnter query (or 'quit'): ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit"]:
                print("Exiting RAG Chatbot. Goodbye!")
                break
            
            res = bot.run(user_input)
            for step in res["steps"]:
                print(f"  [Thought]     : {step['thought']}")
                print(f"  [Action]      : {step['action']}({step['tool_input']})")
                print(f"  [Observation] : {step['observation']}")
            print(f"\n[Final Response]:\n{res['final_answer']}")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break

if __name__ == "__main__":
    main()
