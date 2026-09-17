from backend.app.agents.graph import orchestrator


questions = [
    "What was the company's revenue in 2025?",
    "What are the major regulatory risks?",
    "What products does the company offer?"
]


for question in questions:

    state = {
        "question": question,
        "case_id": 1
    }

    result = orchestrator(state)

    print(f"\nQuestion: {question}")
    print(f"Route: {result['route']}")