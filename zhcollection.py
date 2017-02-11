#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-02-05 14:04:22
# @Author  : Your Name (you@example.org)
# @Link    : http://example.org
# @Version : $Id$

from spider import SpiderHTML
import sys, urllib2, os, random, re, time

url = 'https://www.zhihu.com/topic/19880444/top-answers?page='
store_path = '/home/ubuntu/zhspider/test'

reload(sys)
sys.setdefaultencoding('utf-8')


class zhCollectionSpider(SpiderHTML):
  def __init__(self, pageStart, pageEnd, url):
    self._url = url
    self._pageStart = int(pageStart)
    self._pageEnd = int(pageEnd) + 1
    self.downloadLimit = 0

  def start(self):
    for page in range(self._pageStart, self._pageEnd):
      url = self._url + str(page)
      content = self.getUrl(url)
      # 精华
      if 'top-answers' in url:
          class_ = "feed-item"
      # 收藏夹
      elif 'collections' in url:
          class_ = "zn-item"
      questionList = content.find_all('div', class_=class_)
      for question in questionList:
        Qtitle = question.find('h2')
        if Qtitle is None:
          continue
        # 问题的标题
        questionStr = Qtitle.a.string
        print questionStr
        Qurl = 'http://www.zhihu.com'+Qtitle.a['href']
        print Qurl
        Qtitle = re.sub(r'[\\/:*?"<>]', '#', Qtitle.a.string)
        print '----getting question:'+Qtitle+'----'
        Qcontent = self.getUrl(Qurl)
        print Qcontent
        answerList = Qcontent.find_all('div', class_='zm-item-answer zm-item-expanded')
        self._processAnswer(answerList, Qtitle)
        break
        time.sleep(5)

  def _processAnswer(self, answerList, Qtitle):
    j = 0
    for answer in answerList:
      j = j + 1
      upvoted = int(answer.find('span', class_='count').string.replace('K', '000'))
      if upvoted < 100:
        pass
      authorInfo = answer.find('div', class_='zm-item-answer-author-info')
      author = {'introduction':'', 'link':''}
      try:
        author['name'] = authorInfo.find('a', class_='author-link').string
        author['introduction'] = str(authorInfo.find('span', class_='bio')['title'])
      except AttributeError:
        author['name'] = '匿名用户' + str(j)
      except TypeError:
        pass

      try:
        author['link'] = authorInfo.find('a', class_='author-link')['href']
      except TypeError:
        pass

      file_name = os.path.join(store_path, Qtitle, 'info', author['name']+'_info.txt')
      if os.path.exists(file_name):
        continue

      self.saveText(file_name, '{introduction}\r\n{link}'.format(**author))
      print '正在获取用户{name}的答案'.format(**author)
      answerContent = answer.find('div', class_='zm-editable-content clearfix')
      if answerContent is None:
        continue

      imgs = answerContent.find_all('img')
      if len(imgs) == 0:
        pass
      else:
        self._getImgFromAnswer(imgs, Qtitle, **author)

  def _getImgFromAnswer(self, imgs, Qtitle, **author):
    i = 0
    for img in imgs:
      if 'inline-image' in img['class']:
        continue
      i = i + 1
      imgUrl = img['src']
      extension = os.path.splitext(imgUrl)[1]
      path_name = os.path.join(store_path, Qtitle, author['name']+'_'+str(i)+extension)
      print "Image_CrawedUrl:", imgUrl
      print "Image_Save_Path:", path_name
      try:
        self.saveImg(imgUrl, path_name)
      except ValueError:
        pass
      except KeyError as e:
        pass
      except Exception, e:
        print str(e)
        pass

if __name__ == '__main__':
  page, limit, paramsNum = 1, 0, len(sys.argv)
  if paramsNum >= 3:
    page, pageEnd = sys.argv[1], sys.argv[2]
  elif paramsNum == 2:
    page = sys.argv[1]
    pageEnd = page
  else:
    page, pageEnd = 1, 1

  spider = zhCollectionSpider(page, pageEnd, url)
  spider.start()

