from backend.app.agents.graph import due_diligence_graph


result = due_diligence_graph.invoke(
    {
        "question": "What financial market risks does Microsoft disclose in its 2025 annual report?",
        "case_id": 13
    }
)

print("\n================ TEST RESULT ================")

print("\nQuestion:")
print(result["question"])

print("\nRoutes:")
print(result.get("routes"))

print("\nAgent Results:")

for agent_result in result.get("agent_answers", []):
    print("\nAgent:", agent_result.get("agent"))

    print("Finding:")
    print(agent_result.get("finding"))

    print("\nSources:")
    for source in agent_result.get("sources", []):
        print(source)

print("\nFinal Answer:")
print(result.get("answer"))

print("\nFinal Sources:")
for source in result.get("sources", []):
    print(source)

print("\n==============================================")