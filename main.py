import feedparser
import urllib3
from bs4 import BeautifulSoup

subscriptionFeedUrl = 'https://v2rayshare.com/feed'
saveDir = 'subscription'
clashFileName = 'clash_sub.yaml'
v2rayFileName = 'vray_sub.txt'

http = urllib3.PoolManager()


def downloadSubscription():
    parsed = feedparser.parse(subscriptionFeedUrl)
    topLink = parsed.entries[0].link
    print(topLink)
    html = getSubscriptionPageHtml(topLink)
    soup = BeautifulSoup(html, 'html.parser')

    matchedStartTag = soup.find('h2', string = '订阅链接')
    if matchedStartTag is None:
        raise '未找到解析目标'

    v2rayTag = matchedStartTag.findNext('strong', string = 'v2ray订阅链接:')
    v2rayLink = v2rayTag.findNext('p').text
    if v2rayLink is not None:
        v2raySubLinks = getSubscriptionPageHtml(v2rayLink)
    clashTag = matchedStartTag.findNext('strong', string = 'clash订阅链接：')
    clashLink = clashTag.findNext('p').text
    if clashLink is not None:
        clashSubLinks = getSubscriptionPageHtml(clashLink)

    #  write to file
    with open(saveDir+'/'+v2rayFileName, 'w', encoding='utf-8') as f:
        f.write(v2raySubLinks)
    with open(saveDir+'/'+clashFileName, 'w', encoding='utf-8') as f:
        f.write(clashSubLinks)


def getSubscriptionPageHtml(url):
    response = http.request('get', url)
    if response.status == 200:
        return response.data.decode('utf-8')
    else:
        return None


if __name__ == '__main__':
    downloadSubscription()
