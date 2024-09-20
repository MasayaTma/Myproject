# -*- coding: utf-8 -*-
"""
Qiitaトレンドのデータを取得し、Azure OpenAIを使用して要約を生成する
"""

import time
import os
from openai import AzureOpenAI
import gradio as gr
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

load_dotenv()

#-------------------AzureOpenAIの情報を.envから読み込み-------------------
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"), 
    api_version=os.getenv("AZURE_API_VERSION"),
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    )

messages = [{'role': 'system', 'content': 'あなたはエンジニアの学校の先生です。次の記事の内容を新人のエンジニアにもわかりやすいように200文字程度の日本語で要約してください。'}]
#-------------------AzureOpenAIのAPI情報とプロンプト-------------------

#-------------------ウェブスクレイピングの動作（webドライバーの起動と入力された情報によるURLの分岐）-------------------
def fetch_qiita_data(mail, password, use_tag, selected_tag):
    SLEEP_TIME = 3
    driver_path = "./chromedriver.exe"  
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # ヘッドレスモードで実行（ブラウザウィンドウを表示しない）

    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("WebDriver initialized")
        #--------タグのチェックボックスを入れたときの処理--------
        if use_tag:
            url = "https://qiita.com/tags/" + selected_tag
            classname = "style-nqak7h"
            driver.get(url)
            time.sleep(SLEEP_TIME)
            row_elements = driver.find_elements(By.CLASS_NAME, classname)
          #--------タグのチェックボックスを入れたときの処理--------
        else:
        #--------タグのチェックボックスを入れていないときの処理--------
            url = "https://qiita.com/trend"
            classname = "style-rb2tso"
            driver.get(url)
            time.sleep(SLEEP_TIME)
            print(f"Accessing {url} with mail: {mail}, password: {password}")
            driver.find_element(By.NAME, "identity").send_keys(mail)
            driver.find_element(By.NAME, "password").send_keys(password)
            driver.find_element(By.CLASS_NAME, "sessions_button--wide").click()
            time.sleep(SLEEP_TIME)
            row_elements = driver.find_elements(By.CLASS_NAME, classname)
        #--------タグのチェックボックスを入れていないときの処理--------


        # ページから記事の情報を取得する
        #リストの中にタイトルとURLをそれぞれ保存する。（空のresultリストはあとで使う）
        result = []
        for i_box in row_elements[:4]:  # 最大4つの要素を取得
            row_data = dict()
            row_data["title"] = i_box.find_element(By.TAG_NAME, "h2").text
            row_data["url"] = i_box.find_element(By.TAG_NAME, "h2").find_element(By.TAG_NAME, "a").get_attribute("href")
            result.append(row_data)

        driver.quit()

       
        # ページの内容をpage_contentに格納する関数（page_contentに内容を渡してG4で要約する）
        #新しいwebドライバーを開いて記事の内容を取得する処理を行っている
        def fetch_page_content(url):
            try:
                new_driver = webdriver.Chrome(service=service, options=chrome_options)
                new_driver.get(url)
                time.sleep(SLEEP_TIME)
                page_content = new_driver.find_element(By.TAG_NAME, "body").text
                new_driver.quit()
                return page_content
            except Exception as e:
                return str(e)


        # 内容を要約する関数(page_contantから記事の内容をもらいGPT4で内容を要約)
        def summarize_content(page_content):
            try:
                #取得した記事の内容をGPTに渡して要約してもらいメッセージに渡して返してもらうらしい
                messages.append({'role': 'user', 'content': page_content})
                response = client.chat.completions.create(messages = messages, model=os.getenv("AZURE_DEPLOYMENT"))
                messages.append({'role': os.getenv("AZURE_DEPLOYMENT"), 'content': response.choices[0].message.content})
                
                return response.choices[0].message.content
            except Exception as e:
                return str(e)    
    
            
        # 各URLの要約を生成(summariesリストに要約を格納)
        summaries = []
        for item in result:
            page_content = fetch_page_content(item["url"])
            summary = summarize_content(page_content)
            summaries.append(summary)

        # 結果をリストに返す（最初に作ったresultにtitle,url,summariesにまとめる）
        result += [{"title": "", "url": "", "summary": ""}] * (4 - len(result))  # 結果が4つ未満の場合、空の要素を追加
        summaries += [""] * (4 - len(summaries))  # 要約が4つ未満の場合、空の要約を追加
        # 各要素のタイトル、URL、要約をタプルとして返す
        return (result[0]["title"], result[0]["url"], summaries[0],
                result[1]["title"], result[1]["url"], summaries[1],
                result[2]["title"], result[2]["url"], summaries[2],
                result[3]["title"], result[3]["url"], summaries[3])

    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return (str(e), "", "", "", "", "", "", "", "", "", "")

# Gradio インターフェースの定義
with gr.Blocks() as iface:
    with gr.Row():
        #--------input側のUI--------
        #ここで入力した内容がスクレイピング処理のfetch_qiita_data(mail, password, use_tag, selected_tag):で参照される
        with gr.Column():
            email = gr.Textbox(label="メール", placeholder="メールアドレスを入力")
            #type=passwordで入力した文字を伏字にする
            password = gr.Textbox(label="パスワード", type="password", placeholder="パスワードを入力")
            use_tag = gr.Checkbox(label="抽出内容を指定する")
            selected_tag = gr.Dropdown(
                choices=[
                    'python', 'javascript', 'powerapps', 'powerautomate', 'powerplatform', 'microsoft', 'vscode',
                    'chatgpt', 'AI', 'azure', 'uipath', 'vba', 'onenote', 'teams', '初心者', '機械学習', '効率化',
                    '自動化', 'スキルチェック', 'その他', 'つぶやき', 'クソコード'
                ],
                label="タグの指定"
            )
        #--------input側のUI--------
        
    #--------output側のUI--------
    #gr.rowで同じ行の中にgr.columnで列を追加しているため一行に4つの項目を表示することができている            
    with gr.Row():
        with gr.Column():
            output1_title = gr.Textbox(label="タイトル1")
            url1 = gr.Textbox(label="URL1")
            summary1 = gr.Textbox(label="要約1")
        with gr.Column():
            output2_title = gr.Textbox(label="タイトル2")
            url2 = gr.Textbox(label="URL2")
            summary2 = gr.Textbox(label="要約2")
        with gr.Column():
            output3_title = gr.Textbox(label="タイトル3")
            url3 = gr.Textbox(label="URL3")
            summary3 = gr.Textbox(label="要約3")
        with gr.Column():
            output4_title = gr.Textbox(label="タイトル4")
            url4 = gr.Textbox(label="URL4")
            summary4 = gr.Textbox(label="要約4")
            #--------output側のUI--------
            
    #--------送信ボタンの処理(inputに入力情報を入れてoutputに抽出した情報と要約した情報を出力する)--------
    btn = gr.Button("送信", elem_id="submit_button")
    btn.click(fetch_qiita_data, inputs=[email, password, use_tag, selected_tag], 
              outputs=[output1_title, url1, summary1, output2_title, url2, summary2, 
                       output3_title, url3, summary3, output4_title, url4, summary4])
    #--------送信ボタンの処理(inputに入力情報を入れてoutputに抽出した情報と要約した情報を出力する)--------
    
iface.launch(share=True)