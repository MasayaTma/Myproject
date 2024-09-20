# -*- coding: utf-8 -*-
"""
Qiitaトレンドのデータを取得する
"""
import time
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font
import tkinter
import tkinter.messagebox as msgbox
import tkinter.ttk as ttk
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


#Tkクラスの作成
root = tkinter.Tk()
#画面サイズ
root.geometry('300x250')
#画面タイトル
root.title('ログインフォーム')
# チェックボタンの状態を格納するための変数を作成
chk_state = tkinter.IntVar()
#ドロップダウンリストに表示するデータ
module = ('python','javascript','powerapps','powerautomate','powerplatform','microsoft','vscode','chatgpt','AI','azure',"uipath",
          'vba','onenote','teams','初心者','機械学習','効率化','自動化','スキルチェック','その他','つぶやき','クソコード')
#ドロップダウンの内容を格納する変数の作成
selected_tag = tkinter.StringVar()

#テキストボックスの作成
lbl_1 = tkinter.Label(text='メールアドレス')
lbl_1.place(x=30, y=10)
txt_1 = tkinter.Entry(width=30)
txt_1.place(x=30,y=30)
lbl_2 = tkinter.Label(text='パスワード')
lbl_2.place(x=30, y=50)
#show=*はテキストを隠してくれるオプション
txt_2 = tkinter.Entry(width=30,show="*")
txt_2.place(x=30,y=70)
# チェックボタン
chk = tkinter.Checkbutton(root, text='抽出内容を指定する',variable=chk_state)
chk.place(x=30, y=110)
#コンボボックス
lbl_3 = tkinter.Label(text='タグの指定')
lbl_3.place(x=30, y=150)
combobox = ttk.Combobox(root, height=5,width=10,justify='left',values=module,textvariable=selected_tag)
combobox.place(x=30,y=170)

#examをグローバル変数として宣言
mail=str("")
password = str("")

#ボタンのクリックイベント
def btnclick():
    #ここでグローバル変数として代入しないとボタンクリック内だけの変数になってしまいログイン情報を飛ばすことができない
    global mail
    global password
    global selected_tag
    global chk_state
    mail=str(txt_1.get())
    password = str(txt_2.get())     
    selected_tag = combobox.get()
    msgbox.showinfo('送信完了', '送信が完了しました')
    root.destroy()

#ボタンの作成
btn = tkinter.Button(root, text='送信', command=btnclick)
btn.place(x=140,y=210)
#表示
root.mainloop()

#ページを開くときの待ち時間の設定とデータを保存するExcelファイルの名前の設定
SLEEP_TIME=3



def onchk():
    global row_elements
    global result
    global XLSX_NAME
    XLSX_NAME = "output/qiita_tags_"+ selected_tag+".xlsx"
    url = "https://qiita.com/tags/" + selected_tag
    classname =("style-nqak7h")
    driver.get(url)
    #直前に指定している3秒待機をここで使う（ページの読み込み待ちの時間）
    time.sleep(SLEEP_TIME)
    #抽出した要素を一度リスト化している。抽出するのはQiitaのこれは見出しのボックスみたいになっている部分(classnameはボタンのクリックイベントで指定)
    result = list()
    row_elements = driver.find_elements(By.CLASS_NAME, classname)   
                     

        
def unchk():
    global row_elements
    global result
    global XLSX_NAME    
    XLSX_NAME = "output/qiita_trend.xlsx"
    url = "https://Qiita.com/trend"
    classname = ("style-rb2tso")
    driver.get(url)
    time.sleep(SLEEP_TIME)
    # NAME属性が”identity”であるHTML要素を取得し、ログインID文字列をキーボード送信
    driver.find_element(By.NAME,"identity").send_keys(mail)
    # NAME属性が”password”であるHTML要素を取得し、パスワード文字列をキーボード送信
    driver.find_element(By.NAME,"password").send_keys(password)
    # CLASS属性が”sessions_button--wide”であるHTML要素を取得してクリック
    driver.find_element(By.CLASS_NAME,"sessions_button--wide").click()       
    #抽出した要素を一度リスト化している。抽出するのはQiitaのstyle-rb2tso（これは見出しのボックスみたいになっている部分）
    result = list()
    row_elements = driver.find_elements(By.CLASS_NAME, classname)   


if __name__=="__main__":
    try:   
        #chromeライバーの起動
        driver_path = "./chromedriver.exe"
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service,)
        #Excelに書き込むときにうまくいかなかったから調べたらBeautiful soupを使うとうまくいくって書いてあったから使ってみた
        #文字化け対策にいろいろやってるけどもしかしたらいらないものがあるかも
        html = driver.page_source
        soup = BeautifulSoup(html,"html.parser")
        
        if chk_state.get():
            onchk()
        else:
            unchk()
        
        for i_box in row_elements:
            row_data = dict()
            row_data["title"]= i_box.find_element(By.TAG_NAME, "h2").text
            row_data["url"] = i_box.find_element(By.TAG_NAME, "h2").find_element(By.TAG_NAME, "a").get_attribute("href")
            row_data["tags"] = i_box.find_element(By.TAG_NAME, "ul").text
            result.append(row_data)
                
        print(result)
        
        #Excelに書き込み
        with pd.ExcelWriter(XLSX_NAME) as writer:
            df = pd.DataFrame(result)
            df.to_excel(writer, index=False)
            
            #ワークブックを開く
            wb =writer.book
            ws = wb.active
            
            #B列を（URL）をハイパーリンクに変換
            for row in ws.iter_rows(min_row=2,max_row=ws.max_row):
                cell =row[1]
                cell.hyperlink = cell.value
                cell.style = "Hyperlink"
            
            wb.save
    
    finally:
        driver.quit()