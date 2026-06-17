from google import genai
from google.genai import types

GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

client = genai.Client()

# Search config (unchanged behavior)
config = types.GenerateContentConfig(
    tools=[types.Tool(google_search=types.GoogleSearch())],
    temperature=0.2,
    top_p=0.8,
    system_instruction="""
        You are a research assistant.
        Always include citations in your answer.
        Use numbered references like [1], [2].
        Base answers on verifiable data.
    """
)

chat = client.chats.create(
    model="gemini-3.5-flash",
    config=config
)

# Commands
commands = {
    "/help": "Show all available commands",
    "/exit": "Exit the chatbot",
    "/clear": "Clear the chat history",
}

print("New chat started type \"exit\" to end chat\n")

while True:

    prompt = input(f"{RESET}\nYou: ")

    # Exit
    if prompt.lower() == "/exit":
        print(f"{RESET}")
        break

    # Clear
    if prompt == "/clear":
        chat = client.chats.create(model="gemini-3.5-flash", config=config)
        print("Chat reset.")
        continue

    # Help
    if prompt == "/help":  
        print()      
        print(f"{'Command':<15} Description")
        print("-" * 50)
        for cmd, desc in commands.items():
            print(f"{cmd:<15} {desc}")
        continue

    # AI response
    try:
        response = chat.send_message(prompt)
    except Exception as e:
        print(f"\nError: {e}")
        continue

    print(f"{BLUE}\nAI: ", end="")
    print(response.text)

    # Metadata (citations)
    metadata = None
    if hasattr(response, "candidates") and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, "grounding_metadata"):
            metadata = candidate.grounding_metadata

    if metadata:
        if metadata.web_search_queries:
            print(f"{GREEN}\nSearch queries executed:")
            for query in metadata.web_search_queries:
                print(f" - {query}")

        if metadata.grounding_chunks:
            print(f"{YELLOW}\nSources:")
            seen = set()
            for chunk in metadata.grounding_chunks:
                url = chunk.web.uri
                if url not in seen:
                    print(f" - {url}")
                    seen.add(url)
