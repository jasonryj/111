import requests
from datetime import datetime, timedelta
from lxml import etree
import pandas as pd
import os
from time import sleep
from random import randint

def parseTime(unformatedTime):
    if '分钟' in unformatedTime:
        minute = int(unformatedTime.split('分钟')[0])
        return datetime.now() - timedelta(minutes=minute)
    elif '小时' in unformatedTime:
        hour = int(unformatedTime.split('小时')[0])
        return datetime.now() - timedelta(hours=hour)
    elif '昨天' in unformatedTime:
        yesterday = datetime.now() - timedelta(days=1)
        time_str = unformatedTime.split('昨天')[1].strip()
        if time_str:
            time_obj = datetime.strptime(time_str, '%H:%M')
            return yesterday.replace(hour=time_obj.hour, minute=time_obj.minute)
        else:
            return yesterday
    else:
        try:
            return datetime.strptime(unformatedTime, '%Y-%m-%d %H:%M')
        except ValueError:
            return None

def dealHtml(html, six_months_ago, data_list, existing_titles):
    results = html.xpath('//div[@class="result-op c-container xpath-log new-pmd"]')
    for result in results:
        title_elements = result.xpath('.//h3/a')
        title = title_elements[0].xpath('string(.)').strip() if title_elements else 'Unknown'
        summary_elements = result.xpath('.//span[@class="c-font-normal c-color-text"]')
        summary = summary_elements[0].xpath('string(.)').strip() if summary_elements else 'Unknown'
        infos = result.xpath('.//div[starts-with(@class,"news-source")]')
        source = infos[0].xpath(".//span/text()")[0] if infos else 'Unknown'
        dateTime_elements = result.xpath('.//span[@class="c-color-gray2 c-font-normal c-gap-right-xsmall"]/text()')

        if dateTime_elements:
            dateTime = parseTime(dateTime_elements[0])
            if dateTime and dateTime < six_months_ago:
                continue  # 跳过旧于六个月的新闻
            elif dateTime and title not in existing_titles:
                existing_titles.add(title)
                data_list.append({
                    'title': title,
                    'source': source,
                    'time': dateTime.strftime('%Y-%m-%d %H:%M') if dateTime else 'Unknown',
                    'summary': summary
                })
        else:
            continue  # 跳过没有时间信息的新闻


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
    'Referer': 'https://www.baidu.com/s?rtt=1&bsst=1&cl=2&tn=news&word=%B0%D9%B6%C8%D0%C2%CE%C5&fr=zhidao'
}

url = 'https://www.baidu.com/s'
params = {
    'ie': 'utf-8',
    'medium': 0,
    'rtt': 1,
    'bsst': 1,
    'rsv_dl': 'news_t_sk',
    'cl': 2,
    'tn': 'news',
    'rsv_bp': 1,
    'oq': '',
    'rsv_btype': 't',
    'f': 8,
}

def doSpider(keyword, sortBy='time'):
    fileName = '{}.xlsx'.format(keyword)
    data_list = []
    existing_titles = set()

    params['wd'] = keyword
    if sortBy == 'time':
        params['rtt'] = 4

    response = requests.get(url=url, params=params, headers=headers)
    html = etree.HTML(response.text)
    six_months_ago = datetime.now() - timedelta(days=180)

    dealHtml(html, six_months_ago, data_list, existing_titles)

    total_elements = html.xpath('//div[@id="header_top_bar"]/span/text()')
    if not total_elements:
        print("未能定位到总页数信息。请检查页面结构是否有变化。")
        

    total = total_elements[0]
    total = total.replace(',', '')
    total = int(total[10:-1])
    pageNum = min(total // 10, 50)

    for page in range(1, pageNum):
        print(f'第 {page} 页\n\n')
        headers['Referer'] = response.url
        params['pn'] = page * 10
        response = requests.get(url=url, headers=headers, params=params)
        html = etree.HTML(response.text)
        dealHtml(html, six_months_ago, data_list, existing_titles)
        sleep(randint(2, 4))

    df = pd.DataFrame(data_list)
    df.to_excel(fileName, index=False)

if __name__ == "__main__":
    doSpider(keyword='裁员', sortBy='time')