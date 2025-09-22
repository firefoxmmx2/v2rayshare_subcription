import feedparser
import urllib3
from bs4 import BeautifulSoup
import yaml
import os

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
    if html is None:
        raise Exception('无法获取订阅网页内容')
    soup = BeautifulSoup(html, 'html.parser')

    matchedStartTag = soup.find('h2', string='订阅链接')
    if matchedStartTag is None:
        raise Exception('未找到解析目标')

    if not os.path.exists(saveDir):
        os.makedirs(saveDir)

    v2rayTag = matchedStartTag.findNext('strong', string='v2ray订阅链接:')
    assert v2rayTag is not None
    v2rayLinkP = v2rayTag.findNext('p')
    v2rayLink = v2rayLinkP.text if v2rayLinkP is not None else None
    if v2rayLink is not None:
        v2raySubLinks = getSubscriptionPageHtml(v2rayLink)
        if v2raySubLinks is None:
            raise Exception('无法获取v2ray订阅链接')
        #  write to file
        with open(saveDir+'/'+v2rayFileName, 'w', encoding='utf-8') as f:
            f.write(v2raySubLinks)

    clashTag = matchedStartTag.findNext('strong', string='clash订阅链接：')
    assert clashTag is not None
    clashLinkP = clashTag.findNext('p')
    clashLink = clashLinkP.text if clashLinkP is not None else None

    if clashLink is not None:
        clashSubLinks = getSubscriptionPageHtml(clashLink)
        if clashSubLinks is None:
            raise Exception('无法获取clash订阅链接')
        # clashYaml add autoproxy
        clashSubLinksYaml = yaml.safe_load(clashSubLinks)
        if not any('自动选择' in proxy for proxy in clashSubLinksYaml['proxy-groups'][0]['proxies']):
            clashSubLinksYaml['proxy-groups'][0]['proxies'].insert(0, '♻️ 自动选择')
            clashSubLinksYaml['proxy-groups'].insert(1, {
                'name': '♻️ 自动选择',
                'type': 'url-test',
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
                'proxies': clashSubLinksYaml['proxy-groups'][0]['proxies'][2:-1]
            })

            clashSubLinks = yaml.dump(clashSubLinksYaml, allow_unicode=True)
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
