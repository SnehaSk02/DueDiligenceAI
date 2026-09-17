from backend.app.agents.graph import due_diligence_graph


def test_multi_agent_graph():

    question = (
        "What products and services does Microsoft provide?"
    )

    result = due_diligence_graph.invoke(
        {
            "question": question,
            "case_id": 13
        }
    )

    print("\nQuestion:")
    print(result["question"])

    print("\nRoutes:")
    print(result.get("routes"))

    print("\nFinal Answer:")
    print(result.get("answer"))

    print("\nFinal Sources:")
    for source in result.get("sources", []):
        print(source)


print("\n==============================================")

if __name__ == "__main__":
    test_multi_agent_graph()