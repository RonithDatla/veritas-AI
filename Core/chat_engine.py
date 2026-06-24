from config import get_config

def create_chat(client, model, mode):
    return client.chats.create(
        model=model,
        config=get_config(mode)
    )

def send_message(chat, message):
    return chat.send_message(message)