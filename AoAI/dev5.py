import os
import json
import gradio as gr
import langchain
from langchain.memory import ConversationBufferMemory
from langchain.schema import ChatMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.chains import ConversationChain
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.document_loaders import UnstructuredURLLoader
from dotenv import load_dotenv
import requests

# .env ファイルから環境変数を読み込む
load_dotenv()

# Bing APIを使用する関数
def web_search(query):
    subscription_key = os.getenv("BING_SUBSCRIPTION_KEY")
    search_url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML"}
    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()
    return search_results

def extract_snippet(search_results):
    snippets = []
    for result in search_results.get("webPages", {}).get("value", []):
        snippets.append(result["snippet"])
    return snippets

def generate_response(user_input):
    search_results = web_search(user_input)
    snippets = extract_snippet(search_results)
    response = "以下の情報が見つかりました:\n" + "\n".join(snippets)
    return response

# -----------------フィードバックを保存する関数-----------------
def save_feedback(user_id, message_id, feedback):
    feedback_file = f"chat_histories/{user_id}_feedback.json"
    try:
        with open(feedback_file, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)
    except FileNotFoundError:
        feedback_data = {}

    feedback_data[message_id] = feedback

    with open(feedback_file, "w", encoding="utf-8") as f:
        json.dump(feedback_data, f, ensure_ascii=False)
# -----------------フィードバックを保存する関数-----------------

urls = "https://qiita.com/shun_sakamoto/items/7944d0ac4d30edf91fde"
loader = WebBaseLoader(urls)
documents = loader.load()
embeddings = AzureOpenAIEmbeddings(
    model="embedding2",
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_API_KEY"),
    api_version=os.getenv("AZURE_API_VERSION"),
    openai_api_type='azure'
)
vectorstore = Chroma.from_documents(documents, embeddings)
index = UnstructuredURLLoader(urls=urls, vectorstore=vectorstore)

# azureの情報（.envから読み込み）
api_type = "azure"
key = os.getenv("AZURE_API_KEY")
version = os.getenv("AZURE_API_VERSION")
endpoint = os.getenv("AZURE_ENDPOINT")

# GPT-4モデルを使用するConversationChainを初期化
model = AzureChatOpenAI(
    openai_api_version=version,
    azure_deployment=os.getenv("AZURE_DEPLOYMENT"),
    azure_endpoint=endpoint,
    api_key=key
)

# chat_historiesフォルダを作成（存在しない場合）
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
    # Bing APIを使用して検索結果を取得
    search_results = web_search(user_input)
    snippets = extract_snippet(search_results)
    bing_response = "以下の情報が見つかりました:\n" + "\n".join(snippets)
    
    # ConversationChainを使用して応答を生成
    assistant_response = conversation.predict(input=user_input)
    
    # Bing APIの結果を応答に追加
    final_response = assistant_response + "\n\n" + bing_response
    return final_response

# 過去の会話履歴を読み込む
user_id = "test_user_id"
conversation_memory = load_conversation_memory(user_id)

# ConversationChainを初期化
template = "あなたはプログラミングに特化したアシスタントです。ユーザーの質問に対して、具体的で正確なコード例や説明を提供してください。"
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

# Gradioインターフェースの定義
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
    feedback = gr.Radio(["Good", "Bad"], label="Feedback")

    def clear_history():
        return []

    def handle_feedback(user_input, chat_history, feedback):
        message_id = len(chat_history) - 1  # 最新のメッセージID
        save_feedback(user_id, message_id, feedback)
        return "", chat_history

    msg.submit(gradio_chat, [msg, chatbot], [msg, chatbot])
    feedback.change(handle_feedback, [msg, chatbot, feedback], [msg, chatbot])
    clear.click(clear_history, None, chatbot)

demo.launch()
