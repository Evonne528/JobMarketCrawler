# <p align="center">招聘网站招聘信息爬虫</p>
## 项目简介
使用Selenium和BeautifulSoup爬取Boss直聘网页招聘信息。
<br />
<br />

## 功能
1. 手机二维码登录后从自己账号设置好的多个求职期望列表页面中获取 title, salary, tags, location, and boss name
2. 获取的信息增量保存于当前时间点的新建csv文件中
3. 维护搜索过的职位信息于zhipin_jobs_all.csv

## Requirements
- Python 3.x
- Selenium
- BeautifulSoup
- ChromeDriverManager

## Setup
Install dependencies:
```python
pip install selenium beautifulsoup4 webdriver_manager
```

## Run the script
```python
cd zhipin_scraper
python zhipin_scraper.py
```
