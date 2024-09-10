 import os
import json
import gradio as gr
import langchain
from langchain.memory import ConversationBufferMemory
from langchain.schema import ChatMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.chains.conversation.base import ConversationChain
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enable langchain debugging
langchain.debug = True

# Retrieve Azure OpenAI credentials from environment variables
api_type = os.getenv("API_TYPE")
key = os.getenv("API_KEY")
version = os.getenv("API_VERSION")
endpoint = os.getenv("AZURE_ENDPOINT")

# Initialize ConversationChain with GPT-4 model
model = AzureChatOpenAI(
    openai_api_version=version,
    azure_deployment='assistant',
    azure_endpoint=endpoint,
    api_key=key
)

# Create chat_histories folder if it doesn't exist
os.makedirs("chat_histories", exist_ok=True)

def load_conversation_memory(user_id):
    try:
        with open(f"chat_histories/{user_id}.json", "r", encoding="utf-8") as f:
            data = f.read()
            messages = json.loads(data)
            chat_memory = ConversationBufferMemory(
                chat_memory=ChatMessageHistory(
                    messages=[
                        ChatMessage(
                            content=msg['content'],
                            role=msg['role'].lower() if msg['role'].lower() in ['system', 'assistant', 'user', 'function', 'tool'] else 'user'
                        )
                        for msg in messages
                    ]
                ),
                return_messages=True
            )
            return chat_memory
    except FileNotFoundError:
        return ConversationBufferMemory(return_messages=True)

def save_conversation_memory(user_id, conversation_memory):
    with open(f"chat_histories/{user_id}.json", "w", encoding="utf-8") as f:
        messages = [
            {
                "role": "user" if msg.type == "human" else "assistant" if msg.type == "ai" else msg.type,
                "content": msg.content
            }
            for msg in conversation_memory.chat_memory.messages
        ]
        f.write(json.dumps(messages, ensure_ascii=False))

def chat(user_input):
    assistant_response = conversation.predict(input=user_input)
    return assistant_response

# Load past conversation history
user_id = "test_user_id"
conversation_memory = load_conversation_memory(user_id)

# Initialize ConversationChain
template = "あなたは親切で万能なアシスタントです。ユーザーの質問に丁寧な口調で答えてください。"
chat_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(template),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

conversation = ConversationChain(
    prompt=chat_prompt,
    llm=model,
    memory=conversation_memory,
)

# Define Gradio interface
def gradio_chat(user_input, chat_history):
    assistant_response = chat(user_input)
    chat_history.append((user_input, assistant_response))
    save_conversation_memory(user_id, conversation.memory)
    return "", chat_history

with gr.Blocks() as demo:
    gr.Markdown("## GPT-4 Chatbot")
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    clear = gr.Button("Clear")

    def clear_history():
        return []

    msg.submit(gradio_chat, [msg, chatbot], [msg, chatbot])
    clear.click(clear_history, None, chatbot)

demo.launch()
