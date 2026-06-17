from google import genai
from google.genai import types
import pandas as pd

def make_table(data):
    try:
        df = pd.DataFrame(data)
        print(df.to_string(index=False))
    except Exception as e:
        print(f"Error creating table: {e}")

GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

client = genai.Client()

# SEARCH CONFIG (short + surface-level)
search_config = types.GenerateContentConfig(
    tools=[types.Tool(google_search=types.GoogleSearch())],
    temperature=0.2,
    top_p=0.8,
    system_instruction="""
        You are a research assistant.

        - Use quick surface-level search
        - Return only 5–6 key factual points
        - Keep answers concise
        - Always include citations like [1], [2]
    """
)

search_chat = client.chats.create(
    model="gemini-2.5-flash",
    config=search_config
)

# FUNCTION CONFIG
function_config = types.GenerateContentConfig(
    tools=[
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="make_table",
                    description="Convert structured data into a table",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "data": types.Schema(
                                type="ARRAY",
                                items=types.Schema(type="OBJECT")
                            )
                        },
                        required=["data"]
                    )
                )
            ]
        )
    ],
    temperature=0.2,
    top_p=0.8,
    system_instruction="""
        Always call make_table when tabular data is appropriate.

        Rules:
        - Max 6 rows
        - Consistent columns
        - No explanation text
    """
)

function_chat = client.chats.create(
    model="gemini-2.5-flash",
    config=function_config
)

commands = {
    "/help": "Show all available commands",
    "/exit": "Exit the chatbot",
    "/clear": "Clear the chat history",
}

def is_table_request(prompt):
    p = prompt.lower()
    return (
        "table" in p or
        "compare" in p or
        "difference" in p or
        "vs" in p or
        "list of" in p
    )

print("New chat started type \"exit\" to end chat\n")

while True:

    prompt = input(f"{RESET}\nYou: ")

    if prompt.lower() == "/exit":
        break

    if prompt == "/clear":
        search_chat = client.chats.create(model="gemini-2.5-flash", config=search_config)
        function_chat = client.chats.create(model="gemini-2.5-flash", config=function_config)
        print("Chat reset.")
        continue

    if prompt == "/help":
        print(f"{'Command':<15} Description")
        print("-" * 50)
        for cmd, desc in commands.items():
            print(f"{cmd:<15} {desc}")
        continue

    if is_table_request(prompt):

        print(f"{BLUE}\nAI (fetching data)...\n")

        # Step 1: Search
        try:
            search_prompt = f"""
Give 5 short factual points only:

{prompt}
"""
            search_response = search_chat.send_message(search_prompt)
        except Exception as e:
            print(f"\nSearch error: {e}")
            continue

        # Safe extraction
        try:
            text_lines = search_response.text.split("\n")[:6]
            text = "\n".join(text_lines)
        except Exception:
            text = search_response.text

        # Metadata capture
        try:
            metadata = search_response.candidates[0].grounding_metadata
        except (AttributeError, IndexError, TypeError):
            metadata = None

        # Step 2: Convert to table
        try:
            table_prompt = f"""
Extract structured table data with consistent columns.

Rules:
- Max 6 rows
- Short values
- Return only structured data

Data:
{text}
"""
            function_response = function_chat.send_message(table_prompt)
            candidate = function_response.candidates[0]

        except Exception as e:
            print(f"\nConversion error: {e}")
            continue

        # Step 3: Execute function
        called = False

        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                called = True
                data = part.function_call.args.get("data")

                if data:
                    print("\nTable:\n")
                    make_table(data)
                else:
                    print("No usable data returned")

        if not called:
            print("\nFallback output:\n")
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    print(part.text)

        # Show sources
        if metadata and metadata.grounding_chunks:
            print(f"{YELLOW}\nSources:")
            seen = set()
            for chunk in metadata.grounding_chunks:
                url = chunk.web.uri
                if url not in seen:
                    print(f" - {url}")
                    seen.add(url)

    else:
        try:
            response = search_chat.send_message(prompt)
        except Exception as e:
            print(f"\nError: {e}")
            continue

        print(f"{BLUE}\nAI: ", end="")
        print(response.text)

        try:
            metadata = response.candidates[0].grounding_metadata
        except (AttributeError, IndexError, TypeError):
            metadata = None

        if metadata:
            if metadata.web_search_queries:
                print(f"{GREEN}\nSearch queries:")
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