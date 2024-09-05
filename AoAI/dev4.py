import os
import gradio as gr
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain_core.messages import HumanMessage, AIMessage

# USER_AGENT環境変数を設定
os.environ["USER_AGENT"] = "my-app"

# Azureの情報
api_type = "azure"
api_key = "adaa6041cc474ed28cbdde56a22483f3"
api_version = "2024-02-15-preview"
azure_endpoint = "https://scraping-test.openai.azure.com/"

# URLから情報の取得
loader = WebBaseLoader("https://learn.microsoft.com/ja-jp/training/paths/describe-azure-management-governance/")
docs = loader.load()

url_list = ["https://learn.microsoft.com/ja-jp/training/modules/describe-cost-management-azure/2-describe-factors-affect-costs-azure",
            "https://learn.microsoft.com/ja-jp/training/modules/describe-cost-management-azure/3-compare-pricing-total-cost-of-ownership-calculators"]
for url in url_list:
    loader = WebBaseLoader(url)
    new_docs = loader.load()
    docs.extend(new_docs)

# embeddingでベクトル化
embeddings = AzureOpenAIEmbeddings(openai_api_type=api_type,
                                   api_key=api_key,
                                   azure_endpoint=azure_endpoint,
                                   api_version=api_version,
                                   azure_deployment="embedding2")

# LangChainにAPIの設定（GPT-4）
llm = AzureChatOpenAI(openai_api_type=api_type,
                      api_key=api_key,
                      azure_endpoint=azure_endpoint,
                      api_version=api_version,
                      azure_deployment="assistant")

# テキストを分割
text_splitter = RecursiveCharacterTextSplitter()
documents = text_splitter.split_documents(docs)
print(f"Split into {len(documents)} documents")

vector = FAISS.from_documents(documents, embeddings)
print("Documents embedded and stored in FAISS vector store")

# 検索結果をLLMに入力
base_prompt = ChatPromptTemplate.from_template("""あなたはMicrosoftサービスの世界トップクラスのサポートです。
                                               質問された内容にはなるべくわかりやすく正確に答え、わからない場合は「わからない」と回答してください。

Answer the following question based only on the provided context:

<context>
{context}
</context>

Question: {input}""")

# create_stuff_documents_chainの引数を修正
document_chain = create_stuff_documents_chain(llm=llm, prompt=base_prompt)

retriever = vector.as_retriever()
retrieval_chain = create_retrieval_chain(retriever, document_chain)
print("Retrieval chain created")

# Gradioインターフェースの定義
def gradio_chat(user_input, chat_history):
    response = retrieval_chain.invoke({"input": user_input})
    assistant_response = response["answer"]
    print(f"User input: {user_input}\nAssistant response: {assistant_response}")
    chat_history.append((user_input, assistant_response))
    return "", chat_history

with gr.Blocks() as demo:
    gr.Markdown("## GPT-4 Chatbot")
    chatbot = gr.Chatbot(height=800)  
    with gr.Row():
        msg = gr.Textbox(show_label=False, placeholder="質問を入力してください...")
        submit_btn = gr.Button("送信")
    clear = gr.Button("Clear")

    def clear_history():
        return []

    submit_btn.click(gradio_chat, [msg, chatbot], [msg, chatbot])
    msg.submit(gradio_chat, [msg, chatbot], [msg, chatbot])
    clear.click(clear_history, None, chatbot)

demo.launch()
