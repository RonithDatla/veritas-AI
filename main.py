from google import genai
from google.genai import types


GREEN = "\033[92m"   # search query
BLUE = "\033[94m"    # AI response
YELLOW = "\033[93m"  # Sources
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

chat = client.chats.create(model="gemini-3.5-flash",config=config)

print("New chat started type \"exit\" to end chat\n")

while True:
    prompt=input(f"{RESET}\nYou: ")

    if prompt.lower()=="exit":
        print(f"{RESET}")
        break
    response=chat.send_message(prompt)
    print(f"{BLUE}\nAI: ", end="")
    print(f"{response.text}")
    metadata = response.candidates[0].grounding_metadata
    if metadata:
        if metadata.web_search_queries:
            print(f"{GREEN}\nSearch queries executed:")
            for query in metadata.web_search_queries:
                print(f" - {query}")

        if metadata.grounding_chunks:
            print(f"{YELLOW}\nSources:")
            for chunk in metadata.grounding_chunks:
                print(f" - [{chunk.web.title}]({chunk.web.uri})")
        
