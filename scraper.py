import os
import random
import time
import json
import requests
import base64
from io import BytesIO
from urllib.parse import urlparse, unquote
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image


class GoogleImageScraper:
    def __init__(self, config):
        self.max_images_per_keyword = config["max_images_per_keyword"]
        self.proxies = config["proxies"]
        self.keywords = config["keywords"]
        self.driver = None
        self.init_driver()

        # 添加多个 User-Agent
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.48"
        ]

    def init_driver(self):
        """初始化 Selenium WebDriver"""
        self.driver = webdriver.Chrome()
        self.driver.get('https://www.google.com/imghp')
        time.sleep(2)

    def scroll_to_load(self, scroll_times=3):
        """滚动页面加载更多内容"""
        for _ in range(scroll_times):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 3))  # 添加随机等待时间

    def get_headers(self):
        """动态获取请求头"""
        return {
            "referer": "https://www.google.com/",
            "user-agent": random.choice(self.user_agents)  # 随机选择 User-Agent
        }

    def get_image_links(self, keyword):
        """获取关键词的图片链接"""
        self.driver.get('https://www.google.com/imghp')
        time.sleep(2)
        search_box = self.driver.find_element(By.NAME, 'q')
        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)
        self.scroll_to_load()

        divs = self.driver.find_elements(By.CLASS_NAME, 'ob5Hkd')
        links = []

        for idx, div in enumerate(divs):
            if len(links) >= self.max_images_per_keyword:
                break
            try:
                hover = ActionChains(self.driver).move_to_element(div)
                hover.perform()
                time.sleep(0.5)
                a_tag = div.find_element(By.TAG_NAME, 'a')
                href = a_tag.get_attribute('href')
                if href:
                    links.append(href)
            except Exception as e:
                print(f"处理第 {idx} 个 div 时出错: {e}")
        return links

    def download_images(self, links, folder_path):
        """下载图片到指定文件夹"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        for idx, link in enumerate(links):
            try:
                self.driver.get(link)
                img = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//img[@jsname="kn3ccd"]'))
                )
                img_src = img.get_attribute('src')
                headers = self.get_headers()  # 获取动态请求头

                if img_src.startswith('data:image'):
                    data = base64.b64decode(img_src.split(',', 1)[1])
                else:
                    # 使用代理下载图片
                    data = requests.get(img_src, headers=headers, proxies=self.proxies).content

                image = Image.open(BytesIO(data))
                img_name = f"{folder_path}/image_{idx + 1}.png"
                image.save(img_name)
                print(f"已保存图片: {img_name}")
            except Exception as e:
                print(f"下载图片时出错: {e}")

    def scrape(self):
        """主爬取流程"""
        for keyword in self.keywords:
            print(f"开始爬取关键词: {keyword}")
            folder_path = f"images/{keyword.replace(' ', '_')}"
            links = self.get_image_links(keyword)
            print(f"关键词 '{keyword}' 获取到 {len(links)} 个链接")
            self.download_images(links, folder_path)
        self.driver.quit()
        print("所有关键词图片爬取完成！")


if __name__ == "__main__":
    # 加载配置文件
    with open("config.json", "r") as f:
        config = json.load(f)

    # 创建爬虫实例并运行
    scraper = GoogleImageScraper(config)
    scraper.scrape()
