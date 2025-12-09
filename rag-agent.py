import chromadb
import openai
import os

# Set environment variable to disable the warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"


def main():
    if not os.path.exists("./chroma/"):
        raise ValueError("Please run `python create-vector.py` first")

    chroma_client = chromadb.PersistentClient(path="./chroma/")
    collection = chroma_client.get_collection(name='concepts')

    client = openai.OpenAI(
        base_url="https://api.fireworks.ai/inference/v1",
        api_key="fw_3ZQM5aAfHYH3obNHgjDZbBRc",
    )

    # Initialize conversation history
    conversation_history = [
        {
            "role": "system",
            "content": (
                "You are a helpful security assistant for NEAR Protocol smart contract development. "
                "Use the provided documentation to answer questions about NEAR security.\n"
                "- If the answer is not in the documentation, say 'I don't know'.\n"
                "- Be concise and as close as possible to the documentation.\n"
                "- You can answer follow-up questions based on previous context."
            )
        }
    ]

    print("🤖 Agent: Hello! I'm your NEAR Protocol security assistant.")
    print("🤖 Agent: Ask me anything about NEAR security, or type 'exit'/'quit' to end the conversation.\n")

    while True:
        user_input = input("👤 User: ").strip()

        # Check for exit commands
        if user_input.lower() in ['exit', 'quit', 'q', 'bye']:
            print("\n🤖 Agent: Goodbye! Stay secure! 🔒")
            break

        # Skip empty input
        if not user_input:
            continue

        # Query vector store for relevant documentation
        relevant_docs = collection.query(query_texts=user_input, n_results=3)

        # Build messages with documentation context
        messages = conversation_history.copy()
        messages.append({
            "role": "documentation",
            "content": "\n\n".join(relevant_docs['documents'][0])
        })
        messages.append({
            "role": "user",
            "content": user_input
        })

        try:
            response = client.chat.completions.create(
                model="accounts/fireworks/models/llama4-maverick-instruct-basic",
                messages=messages,
            )

            agent_response = response.choices[0].message.content
            print(f"\n🤖 Agent: {agent_response}\n")

            # Add to conversation history for context
            conversation_history.append({
                "role": "user",
                "content": user_input
            })
            conversation_history.append({
                "role": "assistant",
                "content": agent_response
            })

        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            print("🤖 Agent: I encountered an error. Please try again or rephrase your question.\n")


if __name__ == "__main__":
    main()
