# encoding: utf-8

from bs4 import BeautifulSoup
import requests
import random
import re
import json
from urllib2 import urlparse, quote


HC360 = "http://s.hc360.com/?w={kw}&mc=seller"
ALIBABA = "http://s.1688.com/selloffer/offer_search.html?keywords={kw}"
JD = "http://search.jd.com/Search?keyword={kw}&enc=utf-8"
ETAO = "http://s.etao.com/search?q={kw}"
TAOBAO = "http://s.taobao.com/search?q={kw}"


LINKS_PER_PAGE = 5
HC_DESCRIPTION = re.compile("var supplyInfoJson = ({.*});")
TAOBAO_LINKS = re.compile("g_page_config = ({.*});")
ALI_DESC = re.compile("varjdesc='(.*)'")
TAOBAO_DESC_URL = re.compile("\"(http://dsc.taobaocdn.com.*?)\"")


def hc360(kw, links_per_page=LINKS_PER_PAGE):
    url = HC360.format(kw=quote(kw.encode("gbk")))
    search = requests.get(url)
    bs_search = BeautifulSoup(search.content, from_encoding="gbk")
    links = [p.a.get("href") for p in bs_search.findAll(
        "p", attrs={"class": "til"}) if p.a]
    if not links:
        raise StopIteration
    for url in {random.choice(links) for i in range(int(links_per_page))}:
        detail = requests.get(url)
        bs_detail = BeautifulSoup(detail.content, from_encoding="gbk")
        title = bs_detail.find(
            "h1", attrs={"class": "item-top-tit"}).text.encode("utf-8")
        images = bs_detail.findAll(
            "a", attrs={"class": "box-img", "href": "javascript:void(0);"})
        img_urls = {json.loads("".join(img.get("rel")).replace("gallery", '"gallery"')
                               .replace("smallimage", '"smallimage"').replace("largeimage", '"largeimage"')
                               .replace("'", '"'))["largeimage"] for img in images}
        supply_info_json = HC_DESCRIPTION.search(
            detail.content.decode("gbk")).groups()[0]
        description = json.loads(supply_info_json)["introduce"]
        yield title, description, img_urls


def jd(kw, links_per_page=LINKS_PER_PAGE):
    url = JD.format(kw=kw.encode("utf-8"))
    search = requests.get(url)
    bs_search = BeautifulSoup(search.content)
    links = [div.a.get("href") for div in bs_search.findAll(
        "div", attrs={"class": "p-name"})]
    if not links:
        raise StopIteration
    for url in {random.choice(links) for i in range(int(links_per_page))}:
        if not url.startswith('http'):
            url = 'http:' + url
        detail = requests.get(url)
        bs_detail = BeautifulSoup(detail.content)
        title_wrap = bs_detail.find("div", attrs={"class": "sku-name"})

        if not title_wrap:
            title_wrap = bs_detail.find("div", attrs={"id": "name"}).find('h1')
        title = title_wrap.text

        img_urls = ['http:' + li.img.get("src").replace("/n5/s54x54_", "/n0/").replace("/n5/", "/n0/") for li in bs_detail.find(
            "div", attrs={"class": "spec-items"}).ul.findAll("li")]
        desc_url_pattern = r"desc: '//(d.3.cn/desc/\d+)"
        pattern = re.compile(desc_url_pattern)
        m = pattern.search(detail.content)
        desc_jsonp_url = 'http://' + m.group(1)
        desc_jsonp = requests.get(desc_jsonp_url)

        desc_content_pattern = r'content":(".*")'
        pattern = re.compile(desc_content_pattern)
        m = pattern.search(desc_jsonp.content)
        desc_content = m.group(1)

        desc_content = json.loads(desc_content)
        description = desc_content.replace('data-lazyload="', 'src="http:')

        yield title, description.decode("utf-8"), img_urls


def etao(kw, links_per_page=LINKS_PER_PAGE):
    url = ETAO.format(kw=quote(kw.encode("gbk")))
    search = requests.get(url)
    bs_search = BeautifulSoup(search.content, from_encoding="gbk")
    links = [urlparse.urljoin(url, div.a.get("href")) for div in bs_search.findAll(
        "div", attrs={"class": "info-panel"})]
    if not links:
        raise StopIteration
    for url in {random.choice(links) for i in range(int(links_per_page))}:
        detail = requests.get(url)
        bs_detail = BeautifulSoup(detail.content, from_encoding="gbk")
        title = bs_detail.find("h1", attrs={"class": "top-title"}).get("title")
        description = bs_detail.find(
            "div", attrs={"class": "product-detail"}).renderContents()
        img_urls = json.loads(bs_detail.find("div", attrs={"class": "product-pic"}).get("data-config").replace("src", '"src"')
                              .replace("stockout", '"stockout"').replace("'", '"'))["src"]
        yield title, description.decode("utf-8"), img_urls


def alibaba(kw, links_per_page=LINKS_PER_PAGE):
    url = ALIBABA.format(kw=quote(kw.encode("gbk")))
    search = requests.get(url)
    bs_search = BeautifulSoup(search.content, from_encoding="gbk")
    links = [a.get("href") for a in bs_search.findAll(
        "a", attrs={"class": "sm-offerShopwindow-titleLink"})]
    if not links:
        raise StopIteration
    for url in {random.choice(links) for i in range(int(links_per_page))}:
        detail = requests.get(url)
        bs_detail = BeautifulSoup(detail.content, from_encoding="gbk")
        title = bs_detail.find("h1", attrs={"class": "d-title"}).text
        img_urls = [json.loads(li.get("data-imgs"))["original"]
                    for li in bs_detail.findAll("li", attrs={"class": "tab-trigger"})]
        description = requests.get(bs_detail.find(
            "div", attrs={"id": "desc-lazyload-container"}).get("data-tfs-url")).content
        description = ALI_DESC.search(description).groups()[0]
        yield title, description.decode("gbk"), img_urls


def taobao(kw, links_per_page=LINKS_PER_PAGE):
    url = TAOBAO.format(kw=quote(kw.encode("gbk")))
    search = requests.get(url)
    bs_search = BeautifulSoup(search.content, from_encoding="gbk")
    g_page_config = json.loads(TAOBAO_LINKS.search(search.content).groups()[0])
    links = [auction["detail_url"]
             for auction in g_page_config["mods"]["itemlist"]["data"]["auctions"]]
    if not links:
        raise StopIteration
    for url in {random.choice(links) for i in range(int(links_per_page))}:
        detail = requests.get(url)
        bs_detail = BeautifulSoup(detail.content, from_encoding="gbk")
        title = bs_detail.title.text
        title = title[:title.find("-")]
        img_urls = [li.find("img").get(
            "data-src") for li in bs_detail.find("ul", attrs={"id": "J_UlThumb"}).findAll("li")]
        img_urls = [img[:img.find(".jpg") + 4] for img in img_urls if img]
        description_url = TAOBAO_DESC_URL.search(detail.content).groups()[0]
        description = requests.get(description_url).content
        description = ALI_DESC.search(description).groups()[0]
        yield title, description.decode("gbk"), img_urls

PRODUCT_SITE = (jd, etao, alibaba, taobao, )

##########################################################################

from readability.readability import Document


CHARSET = re.compile("charset=\"?(.*?)\"")
LINKS = re.compile("<a.*</a>", re.S)


class NewsCapturer(object):

    def __init__(self, site, encoding="utf-8"):
        self.site = site
        self.encoding = encoding

    def get_links(self, search, links_per_page):
        raise NotImplementedError

    def get_encoding(self, content):
        encoding = CHARSET.search(content).groups()[0]
        if not encoding:
            encoding = "utf-8"
        return encoding

    def get_info(self, kws, links_per_page):
        for kw in kws:
            url = self.site.format(kw=quote(kw.encode(self.encoding)))
            search = requests.get(url).content
            bs_search = BeautifulSoup(search, from_encoding=self.encoding)
            links = self.get_links(bs_search)
            for url in {random.choice(links) for i in range(int(links_per_page))}:
                detail = requests.get(url).content
                document = Document(detail, url=url)
                description = document.summary()
                title = document.short_title()
                yield title, LINKS.sub("", description)


class BaiduNewsCapturer(NewsCapturer):

    def get_links(self, bs_search):
        links = [li.find("a").get("href")
                 for li in bs_search.findAll("li", attrs={"class": "result"})]
        return links

baidu_news = BaiduNewsCapturer(
    "http://news.baidu.com/ns?word={kw}&bs={kw}&sr=0&cl=2&rn=20&tn=news&ct=1&clk=sortbyrel", "utf-8")


class SinaNewsCapturer(NewsCapturer):

    def get_links(self, bs_search):
        links = [div.find("a").get("href") for div in bs_search.findAll(
            "div", attrs={"class": "box-result"})]
        return links

sina_news = SinaNewsCapturer(
    "http://search.sina.com.cn/?q={kw}&c=news&from=channel", "gbk")

NEWS_SITE = (baidu_news, sina_news)
