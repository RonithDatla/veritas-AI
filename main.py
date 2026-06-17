from google import genai
from google.genai import types

GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

client = genai.Client()

config = types.GenerateContentConfig(
    tools=[types.Tool(google_search=types.GoogleSearch())],
    temperature=0.2,
    top_p=0.8,
    system_instruction="""
        You are a research assistant.
        Always include citations in your answer.
        Use numbered references like [1], [2].
        Base answers on verifiable data.

        Table rules:
        - Use markdown-style tables with | separators
        - Ensure columns are aligned and consistent
        - Include a header row and separator row
        - Keep text concise to maintain alignment
        - Do not break formatting
        - use the same number of charecters for each cell of the column and ensure it is equal to the number of charecters in the header of the column
        - Do not include extra explanations inside the table
        Always ensure tables are clean and readable in a plain text terminal.

        you must be truthfull about the data even if you contradict the user.
        you are not to provide or create any unsafe unethical content.
    """
)

chat = client.chats.create(
    model="gemini-3.5-flash",
    config=config
)

commands = {
    "/help": "Show all available commands",
    "/exit": "Exit the chatbot",
    "/clear": "Clear the chat history",
}

print("New chat started type \"exit\" to end chat\n")

while True:

    prompt = input(f"{RESET}\nYou: ")

    if prompt.lower() == "/exit":
        print(f"{RESET}")
        break

    if prompt == "/clear":
        chat = client.chats.create(model="gemini-3.5-flash", config=config)
        print("Chat reset.")
        continue

    if prompt == "/help":  
        print()      
        print(f"{'Command':<15} Description")
        print("-" * 50)
        for cmd, desc in commands.items():
            print(f"{cmd:<15} {desc}")
        continue

    try:
        response = chat.send_message(prompt)
    except Exception as e:
        print(f"\nError: {e}")
        continue

    print(f"{BLUE}\nAI: ", end="")
    print(response.text)

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
                if hasattr(chunk, "web") and hasattr(chunk.web, "uri"):
                    url = chunk.web.uri
                    title = getattr(chunk.web, "title", url)
                    if url not in seen:
                        print(f" - {title} ({url})")
                        seen.add(url)