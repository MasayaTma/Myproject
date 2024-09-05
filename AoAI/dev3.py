import os
import json
import csv
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
from langchain.chains import ConversationChain

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
embeddings = AzureOpenAIEmbeddings(model="embedding2",
                                   azure_endpoint="https://scraping-test.openai.azure.com/",
                                   api_key="adaa6041cc474ed28cbdde56a22483f3",
                                   api_version="2024-02-15-preview",
                                   openai_api_type='azure')
vectorstore = Chroma.from_documents(documents, embeddings)
index = UnstructuredURLLoader(urls=urls, vectorstore=vectorstore)

# langchainのデバッグを有効化
# langchain.debug = True

# azureの情報
api_type = "azure"
key = "adaa6041cc474ed28cbdde56a22483f3"
version = "2024-02-15-preview"
endpoint = "https://scraping-test.openai.azure.com/"

# GPT-4モデルを使用するConversationChainを初期化
model = AzureChatOpenAI(
    openai_api_version=version,
    azure_deployment='assistant-2',
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
    assistant_response = conversation.predict(input=user_input)
    return assistant_response

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

def handle_feedback(message_id, feedback, chat_history):
    save_feedback(user_id, message_id, feedback)
    return chat_history

def export_to_csv(user_id):
    conversation_file = f"chat_histories/{user_id}.json"
    feedback_file = f"chat_histories/{user_id}_feedback.json"
    csv_file = f"chat_histories/{user_id}_history.csv"

    try:
        with open(conversation_file, "r", encoding="utf-8") as f:
            conversation_data = json.load(f)
    except FileNotFoundError:
        conversation_data = []

    try:
        with open(feedback_file, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)
    except FileNotFoundError:
        feedback_data = {}

    with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["ID", "Request", "Response", "Feedback"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for i, msg in enumerate(conversation_data):
            if msg["role"] == "user":
                request = msg["content"]
                response = conversation_data[i + 1]["content"] if i + 1 < len(conversation_data) else ""
                feedback = feedback_data.get(str(i), "")
                writer.writerow({"ID": i, "Request": request, "Response": response, "Feedback": feedback})

    return csv_file

with gr.Blocks() as demo:
    gr.Markdown("## GPT-4 Chatbot")
    chatbot = gr.Chatbot(height=600)  # チャットボットの高さを設定
    msg = gr.Textbox()
    clear = gr.Button("Clear")
    feedback_msg_id = gr.Number(label="Message ID", value=0)
    feedback = gr.Radio(["Good", "Bad"], label="Feedback")
    submit_feedback = gr.Button("Submit Feedback")
    export_csv = gr.Button("Export to CSV")

    def clear_history():
        return []

    def handle_feedback_ui(feedback_msg_id, feedback, chat_history):
        message_id = int(feedback_msg_id)
        save_feedback(user_id, message_id, feedback)
        return chat_history

    def export_csv_ui():
        csv_file = export_to_csv(user_id)
        return csv_file

    msg.submit(gradio_chat, [msg, chatbot], [msg, chatbot])
    submit_feedback.click(handle_feedback_ui, [feedback_msg_id, feedback, chatbot], [chatbot])
    clear.click(clear_history, None, chatbot)
    export_csv.click(export_csv_ui)

    def update_feedback_ui(chat_history):
        feedback_ui = []
        for i, (user_msg, assistant_msg) in enumerate(chat_history):
            feedback_ui.append(gr.Markdown(f"### メッセージ {i+1}"))
            feedback_ui.append(gr.Markdown(f"ID: {i+1}"))
            feedback_ui.append(gr.Markdown(user_msg))
            feedback_ui.append(gr.Markdown(assistant_msg))
        return feedback_ui

    demo.load(update_feedback_ui, inputs=[chatbot], outputs=[chatbot])

demo.launch()
