import chromadb.config
import mwclient
import mwparserfromhell
import pandas as pd
import tiktoken
from openai import AzureOpenAI
import chromadb
from chromadb.utils import embedding_functions
import datetime
from datetime import timezone
from dateutil.tz import *
import pytz


def aware_utcnow():
    return datetime.now(timezone.utc)
def aware_utcfromtimestamp(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc)
def naive_utcnow():
    return aware_utcnow().replace(tzinfo=None)
def naive_utcfromtimestamp(timestamp):
    return aware_utcfromtimestamp(timestamp).replace(tzinfo=None)

# timestamp = aware_utcnow()
    
#azureの情報
api_type = "azure"
api_key= "adaa6041cc474ed28cbdde56a22483f3"
api_version="2024-02-15-preview"
azure_endpoint="https://scraping-test.openai.azure.com/"

#wikipediaに接続して指定されたタイトルを取得
#テキスト解析して保存してループして空白の削除をしていい感じに変換するらしい
def fetch_wikipedia_sections(title: str) -> pd.DataFrame:
    site = mwclient.Site("ja.wikipedia.org")
    page = site.pages[title]
    wikitext = page.text()
    parsed_wikitext = mwparserfromhell.parse(wikitext)

    section_data = []
    for section in parsed_wikitext.get_sections():
        headings = section.filter_headings()
        if not headings:
            continue
        heading_text = headings[0].title.strip()
        section_text = section.strip_code().strip()
        section_data.append({"heading": heading_text, "content": section_text})

    return pd.DataFrame(section_data)
#指定したタイトルから抜いてくるけど脚注や注釈、出店、参考文献、関連項目、外部リンクは抜かないよ！
title = "スティーヴィー・ワンダー"
df = fetch_wikipedia_sections(title)
df = df[~df["heading"].isin(["脚注", "注釈", "出典", "参考文献", "関連項目", "外部リンク"])]

# print(df)

#トークン数の計測
GPT_MODEL = "testgpt4"

def num_tokens(text: str, model: str = GPT_MODEL) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

df['num_tokens'] = df['content'].apply(num_tokens)
#print(df)

#Embeddingを使ったベクトルの作成
client = AzureOpenAI(
    api_key= api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint
)

EMBEDDING_MODEL = "embedding2"  # OpenAI's best embeddings as of Apr 2023
BATCH_SIZE = 1000  # you can submit up to 2048 embedding inputs per request

#openai 1.xのコード
def create_embeddings(items):
    embeddings = []
    for batch_start in range(0, len(items), BATCH_SIZE):
        batch_end = batch_start + BATCH_SIZE
        batch = items[batch_start:batch_end]
        # print(f"Batch {batch_start} to {batch_end-1}")
        response = client.embeddings.create(input=batch,model=EMBEDDING_MODEL)
        batch_embeddings = [e.embedding for e in response.data]
        embeddings.extend(batch_embeddings)
        
    df = pd.DataFrame({"text": items, "embedding": embeddings})
    return df

items = df["content"].to_list()
df_embedding = create_embeddings(items)

#print(df_embedding)


openai_ef = embedding_functions.OpenAIEmbeddingFunction(
api_key="adaa6041cc474ed28cbdde56a22483f3",
api_base="https://scraping-test.openai.azure.com/",
api_type="azure",
model_name="embedding2",
api_version="2024-02-15-preview"
)


# ChromaDBクライアントの作成
chroma_client = chromadb.EphemeralClient()
chroma_client = chromadb.PersistentClient(path='./chroma_persistence')
collection = chroma_client.get_or_create_collection(name="stevie_collection",embedding_function=openai_ef)
# Embeddingを作成する関数
def create_embeddings(items):
    embeddings = []
    for batch_start in range(0, len(items), BATCH_SIZE):
        batch_end = batch_start + BATCH_SIZE
        batch = items[batch_start:batch_end]
        response = client.embeddings.create(input=batch, model=EMBEDDING_MODEL)
        batch_embeddings = [e.embedding for e in response.data]
        embeddings.extend(batch_embeddings)
        
    df = pd.DataFrame({"text": items, "embedding": embeddings})
    return df

# Embeddingデータフレームの作成
items = df["content"].to_list()
df_embedding = create_embeddings(items)

# ChromaDBに保存する関数
def save_embeddings_to_chromadb(df, chroma_client, collection_name,):
    # コレクションの作成または取得
    collection = chroma_client.get_or_create_collection(collection_name)
    
    # Embeddingの保存
    for index, row in df.iterrows():
        collection.add(
            ids=str(index),  # 一意なID
            embeddings=row['embedding'],  # Embeddingベクトル
            metadatas={"text": row['text']}  # メタデータとして元のテキストを保存
        )

# EmbeddingをChromaDBに保存
save_embeddings_to_chromadb(df_embedding, chroma_client, "stevie_collection")

#chromaに対しての問い合わせ
def query_collection(
    query: str,
    collection: chromadb.api.models.Collection.Collection, 
    max_results: int = 100)-> tuple[list[str], list[float]]:
    results = collection.query(query_texts=query, n_results=max_results, include=['documents', 'distances'])
    strings = results['documents'][0]
    relatednesses = [1 - x for x in results['distances'][0]]
    return strings, relatednesses

strings, relatednesses = query_collection(
    collection=collection,
    query="スティービーは日本武道館で何回公演している？",
    max_results=3,
)

for string, relatedness in zip(strings, relatednesses):
    print(f"{relatedness=:.3f}")
    print(string)

def query_message(
    query: str,
    collection: chromadb.api.models.Collection.Collection,
    model: str,
    token_budget: int
) -> str:
    strings, relatednesses = query_collection(query, collection, max_results=3)
    introduction = '以下の記事を使って質問に答えてください。もし答えが見つからない場合、「データベースには答えがありませんでした。」 と返答してください。\n\n# 記事'
    question = f"\n\n# 質問\n {query}"
    message = introduction
    for string in strings:
        next_article = f'\n{string}\n"""'
        if (
            num_tokens(message + next_article + question, model=model)
            > token_budget
        ):
            break
        else:
            message += next_article
    return message + question

def ask(
    query: str,
    collection = collection,
    model: str = "testgpt4",
    token_budget: int = 4096 - 500,
    print_message: bool = False,
) -> str:
    """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
    message = query_message(query, collection, model=model, token_budget=token_budget)
    if print_message:
        print(message)
    messages = [
        {"role": "system", "content": "スティービー・ワンダーに関する質問に答えます。"},
        {"role": "user", "content": message},
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0
    )
    response_message = response.choices[0].message.content
    return response_message

# ここに ask 関数を呼び出す部分を追加します
response = ask("スティービーの武道館公演の回数を教えてください。")
print(response)