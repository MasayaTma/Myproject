# -*- coding: utf-8 -*-

"""
Githubトレンドのデータを取得する
"""
import requests
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

SLEEP_TIME = 3
CSV_NAME = "output/github_ranking.csv"


if __name__=="__main__":
    try:
        driver_path = "./chromedriver.exe"
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service,)
        url = "https://github.com/trending"
        driver.get(url)
        time.sleep(SLEEP_TIME)

        result = list()
        box_row_elements = driver.find_elements(By.CLASS_NAME, "Box-row")        
        for i_box in box_row_elements:
            row_data = dict()
            row_data["title"]= i_box.find_element(By.TAG_NAME, "h2").text            
            row_data["url"] = i_box.find_element(By.TAG_NAME, "h2").find_element(By.TAG_NAME, "a").get_attribute("href")
            lang_elements = i_box.find_elements(By.CSS_SELECTOR, ".d-inline-block.ml-0.mr-3")
            row_data["lang"] = lang_elements[0].text if len(lang_elements) == 1 else None
            row_data["total_star"] = i_box.find_elements(By.CSS_SELECTOR, ".Link--muted.d-inline-block.mr-3")[0].text
            row_data["fork"] = i_box.find_elements(By.CSS_SELECTOR, ".Link--muted.d-inline-block.mr-3")[1].text
            row_data["todays_star"] = i_box.find_element(By.CSS_SELECTOR, ".d-inline-block.float-sm-right").text.replace("stars today", "")
            result.append(row_data)
        
        print(result)

        pd.DataFrame(result).to_csv(CSV_NAME, index=False)
    finally:
        driver.quit()