"""
Fetches RouteAI YouTube channel videos and saves to data.json.
Uses only Python stdlib — no pip install needed.
"""
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError

CHANNEL_URL = 'https://www.youtube.com/@routeai/videos'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def fetch(url, timeout=15):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', errors='replace')


def get_channel_id(html):
    for pat in [
        r'"channelId"\s*:\s*"(UC[^"]{20,})"',
        r'"externalChannelId"\s*:\s*"(UC[^"]{20,})"',
        r'channel/(UC[A-Za-z0-9_-]{22})',
    ]:
        m = re.search(pat, html)
        if m:
            return m.group(1)
    return None


def fetch_rss(channel_id):
    rss_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
    xml_text = fetch(rss_url)

    NS = {
        'atom':  'http://www.w3.org/2005/Atom',
        'yt':    'http://www.youtube.com/xml/schemas/2015',
        'media': 'http://search.yahoo.com/mrss/',
    }

    root = ET.fromstring(xml_text)
    videos = []

    for entry in root.findall('atom:entry', NS):
        vid_id = entry.findtext('yt:videoId', namespaces=NS)
        title  = entry.findtext('atom:title', namespaces=NS)
        pub    = entry.findtext('atom:published', namespaces=NS)

        views = None
        stats = entry.find('media:group/media:community/media:statistics', NS)
        if stats is not None:
            try:
                views = int(stats.get('views', 0))
            except ValueError:
                pass

        if vid_id:
            videos.append({
                'id':          vid_id,
                'title':       title or '',
                'publishedAt': pub or '',
                'views':       views,
                'thumb':       f'https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg',
                'url':         f'https://www.youtube.com/watch?v={vid_id}',
            })

    return videos


def main():
    print('📡 Fetching YouTube channel page…')
    html = fetch(CHANNEL_URL)

    channel_id = get_channel_id(html)
    if not channel_id:
        raise RuntimeError('Could not find channel ID in page HTML')
    print(f'✅ Channel ID: {channel_id}')

    print('📋 Fetching RSS feed…')
    videos = fetch_rss(channel_id)
    print(f'✅ Found {len(videos)} videos')

    data = {
        'updated':   datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'channelId': channel_id,
        'videos':    videos,
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print('💾 Saved data.json')


if __name__ == '__main__':
    main()
