from backend.app.agents.graph import due_diligence_graph


def test_multi_agent_graph():

    question = (
        "What was Microsoft's revenue in 2025?"
    )

    result = due_diligence_graph.invoke(
        {
            "question": question,
            "case_id": 13
        }
    )
    print("\nDEBUG FINAL RESULT KEYS:")
    print(result.keys())

    print("\nDEBUG FINAL RETRIEVED EVIDENCE:")
    print(result.get("retrieved_evidence"))

    print("\nQuestion:")
    print(result["question"])

    print("\nRoutes:")
    print(result.get("routes"))

    print("\nFinal Answer:")
    print(result.get("answer"))

    print("\nFinal Sources:")
    for source in result.get("sources", []):
        print(source)
    print("\nRetrieved Evidence:")
    retrieved_evidence = result.get("retrieved_evidence", [])
    for agent_evidence in retrieved_evidence:
        print(f"\nAgent: {agent_evidence.get('agent')}")

        for chunk in agent_evidence.get("chunks", []):
            print(
                f"Page: {chunk.get('page_number')} | "
                f"Chunk: {chunk.get('chunk_index')} | "
                f"Score: {chunk.get('score')}"
            )
            print(f"Text: {chunk.get('text')}")


print("\n==============================================")

if __name__ == "__main__":
    test_multi_agent_graph()