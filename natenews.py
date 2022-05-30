from bs4 import BeautifulSoup
import requests
import pandas as pd
from urllib.parse import urlparse, parse_qs
import datetime

def get_news_list(date: str, week: bool) -> pd.DataFrame:
    """
    Args:
        date (str): yyyymmdd
        week (bool): is a weekly unit

    Returns:
        pd.DataFrame: news list dataframe
    """
    url = f"https://news.nate.com/rank/cmt?sc=&p={'week' if week else 'day'}&date={date}"
    bs = BeautifulSoup(requests.get(url).text, "html5lib")
    tail = bs.select(".mduSubject > *:has(.mduRank)")
    def extract_tail_element(e) -> dict:
        a = e.select("a")[0]
        ems = e.select("em")
        return {
            "rank": int(ems[0].text),
            "comment": int(ems[1].text.replace(",", "")),
            "title": a.text,
            "url": a["href"]
        }
    tail = map(extract_tail_element, tail)
    head = bs.select(".mduSubjectList")
    def extract_head_element(e) -> dict:
        ems = e.select("em")
        a = e.select("a")[0]
        return {
            "rank": int(ems[0].text),
            "comment": int(ems[1].text.replace(",", "")),
            "title": a.select("strong")[0].text,
            "url": a["href"]
        }
    head = map(extract_head_element, head)
    result = pd.DataFrame(list(head) + list(tail))
    result.url = "https:" + result.url
    return result

def get_news_comments(url: str, page: int) -> pd.DataFrame:
    """
    Example:
    ```python
        df = get_news_comments("https://news.nate.com/view/20220530n31323?mid=n1006", 3)
    ```
    Args:
        url (str): nate news url
        page (int): comments page no.

    Returns:
        pd.DataFrame: comments
    """
    url = urlparse(url)
    artc_sq = url.path.split("/")[-1]
    mid = parse_qs(url.query)["mid"][0]
    comment_url = f"https://comm.news.nate.com/Comment/ArticleComment/List?artc_sq={artc_sq}&order=&cmtr_fl=0&prebest=0&clean_idx=&user_nm=&fold=&mid={mid}&domain=&argList=0&best=0&return_sq=&connectAuth=N&page={page}"
    bs = BeautifulSoup(requests.get(comment_url).text, "html5lib")
    cmt_items = bs.select(".cmt_item")
    def extract_comment(e):
        name = e.select(".nameui")[0].text.rstrip()
        date = datetime.datetime.strptime(artc_sq[:4] + " " +e.select(".date")[0].text[2:], "%Y %m.%d %H:%M")
        text = e.select(".usertxt")[0].text.strip()
        up, down = map(lambda e: int(e.text), e.select(".upDown > .line > strong"))
        return {
            "name": name,
            "date": date,
            "text": text,
            "up": up,
            "down": down
        }
    return pd.DataFrame(map(extract_comment, cmt_items))