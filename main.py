import feedparser
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
import yaml
import os

# 禁用 SSL 证书警告
urllib3.disable_warnings(InsecureRequestWarning)

subscriptionFeedUrl = 'https://v2rayshare.com/feed'
saveDir = 'subscription'
clashFileName = 'clash_sub.yaml'
v2rayFileName = 'vray_sub.txt'
mihomoFileName = 'mihomo_sub.yaml'

http = urllib3.PoolManager()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def process_yaml_subscription(sub_content: str, add_auto_proxy: bool = False) -> str:
    """处理 YAML 订阅内容：添加 cipher 字段，可选添加自动选择代理组"""
    data = yaml.safe_load(sub_content)
    
    if 'proxies' in data:
        for proxy in data['proxies']:
            if 'cipher' not in proxy:
                proxy_type = proxy.get('type', '').lower()
                if proxy_type == 'ss':
                    proxy['cipher'] = 'aes-256-cfb'
                elif proxy_type == 'vmess':
                    proxy['cipher'] = 'auto'
    
    if add_auto_proxy and 'proxy-groups' in data:
        first_group = data['proxy-groups'][0]
        if not any('自动选择' in p for p in first_group.get('proxies', [])):
            first_group['proxies'].insert(0, '自动选择')
            data['proxy-groups'].insert(1, {
                'name': '自动选择',
                'type': 'url-test',
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
                'proxies': first_group['proxies'][2:-1]
            })
    
    return yaml.dump(data, allow_unicode=True)


def download_subscription(soup: BeautifulSoup, tag_text: str, filename: str, is_yaml: bool = False, add_auto_proxy: bool = False) -> bool:
    """下载单个订阅，返回是否成功"""
    tag = soup.find('h2', string='订阅链接')
    if not tag:
        return False
    
    strong_tag = tag.find_next('strong', string=tag_text)
    if not strong_tag:
        return False
    
    link_p = strong_tag.find_next('p')
    link = ''.join(link_p.text.split()) if link_p else None
    if not link:
        return False
    
    print(f"  {tag_text.replace('订阅链接：', '').replace('订阅链接:', '')}链接: {link}")
    sub_content = getSubscriptionPageHtml(link)
    if not sub_content:
        print(f"  {tag_text.replace('订阅链接：', '').replace('订阅链接:', '')}链接404，尝试更早的条目")
        return False
    
    if is_yaml:
        sub_content = process_yaml_subscription(sub_content, add_auto_proxy)
    
    with open(saveDir+'/'+filename, 'w', encoding='utf-8') as f:
        f.write(sub_content)
    print(f"  {tag_text.replace('订阅链接：', '').replace('订阅链接:', '')}下载成功")
    return True


def downloadSubscription() -> None:
    parsed = feedparser.parse(subscriptionFeedUrl)
    
    results = {
        'v2ray': {'tag': 'v2ray订阅链接:', 'file': v2rayFileName, 'is_yaml': False},
        'clash': {'tag': 'clash订阅链接：', 'file': clashFileName, 'is_yaml': True, 'auto_proxy': True},
        'mihomo': {'tag': 'Mihomo订阅链接：', 'file': mihomoFileName, 'is_yaml': True, 'auto_proxy': False},
    }
    success = {k: False for k in results}
    
    for entry in parsed.entries[:10]:
        topLink = entry.link
        print(f"\n尝试获取: {topLink}")
        html = getSubscriptionPageHtml(topLink)
        if not html:
            continue
        
        soup = BeautifulSoup(html, 'html.parser')
        if not soup.find('h2', string='订阅链接'):
            continue
        
        if not os.path.exists(saveDir):
            os.makedirs(saveDir)
        
        for name, cfg in results.items():
            if success[name]:
                continue
            if download_subscription(
                soup, 
                cfg['tag'], 
                cfg['file'], 
                cfg.get('is_yaml', False),
                cfg.get('auto_proxy', False)
            ):
                success[name] = True
        
        if all(success.values()):
            break
    
    print(f"\n=== 下载完成 ===")
    for name in success:
        print(f"{name}: {'OK' if success[name] else 'FAIL'}")


def getSubscriptionPageHtml(url: str, retries: int = 3) -> str | None:
    """下载订阅页面，支持重试机制"""
    for attempt in range(retries):
        try:
            response = http.request('get', url, headers=headers, timeout=10)
            if response.status == 200:
                return response.data.decode('utf-8')
        except Exception as e:
            if attempt < retries - 1:
                print(f"  重试 {attempt + 1}/{retries}: {e}")
    return None


if __name__ == '__main__':
    downloadSubscription()
