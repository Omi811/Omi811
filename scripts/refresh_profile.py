"""Render repository-hosted profile cards from public GitHub REST data.

Run from any directory with Python 3. No Vercel account or PAT is needed.
The optional GITHUB_TOKEN is used only with api.github.com, e.g. in Actions.
"""
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import json, os, urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = 'Omi811'

def fetch(path):
    headers = {'User-Agent':'Omi811-public-profile-cards','Accept':'application/vnd.github+json'}
    if os.getenv('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    with urllib.request.urlopen(urllib.request.Request('https://api.github.com/'+path, headers=headers), timeout=25) as response:
        return json.load(response)

def card(title,description,body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="520" height="250" viewBox="0 0 520 250" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc><rect x="1" y="1" width="518" height="248" rx="18" fill="#101720" stroke="#273648"/><g font-family="Arial,Helvetica,sans-serif"><text x="27" y="37" fill="#a9c7e5" font-size="12" letter-spacing="1.2">{escape(title)}</text>{body}<text x="27" y="227" fill="#93a4b8" font-size="11">Public GitHub snapshot · {datetime.now(timezone.utc).strftime('%Y-%m-%d')} UTC</text></g></svg>'''

def main():
    profile = fetch('users/'+USER)
    repos=[]; page=1
    while True:
        batch=fetch(f'users/{USER}/repos?type=owner&amp;per_page=100&amp;page={page}'.replace('&amp;','&'))
        repos.extend(batch)
        if len(batch)<100:break
        page+=1
    originals=[r for r in repos if not r['fork']]
    languages=Counter(r['language'] for r in originals if r.get('language'))
    metrics=[(profile['public_repos'],'PUBLIC REPOS'),(len(originals),'ORIGINAL REPOS'),(profile['followers'],'FOLLOWERS')]
    body='<text x="27" y="64" fill="#b2bccb" font-size="12">Independent engineering, in public.</text>'
    for index,(number,label) in enumerate(metrics):
        x=27+index*166
        body+=f'<text x="{x}" y="132" fill="#f3f6fb" font-size="42" font-weight="700">{number}</text><text x="{x}" y="158" fill="#96a8bd" font-size="10" letter-spacing=".6">{label}</text>'
    body+='<text x="27" y="192" fill="#9dc2ad" font-size="11">Explore repositories and activity on GitHub ↗</text>'
    overview=card('ENGINEERING ACTIVITY',f'{USER}: {profile["public_repos"]} public repositories, {len(originals)} non-fork repositories, {profile["followers"]} followers.',body)
    body='<text x="27" y="63" fill="#b2bccb" font-size="11">Non-fork public repos, grouped by primary language</text>'
    total=sum(languages.values()) or 1
    for index,(lang,count) in enumerate(languages.most_common(4)):
        y=93+index*29
        body+=f'<text x="27" y="{y}" fill="#d6dfeb" font-size="12">{escape(lang)}</text><rect x="133" y="{y-9}" width="300" height="8" rx="4" fill="#273343"/><rect x="133" y="{y-9}" width="{300*count/total:.1f}" height="8" rx="4" fill="#93b9d9"/><text x="451" y="{y}" fill="#d6dfeb" font-size="12">{count}</text>'
    mix=card('LANGUAGE MIX',', '.join(f'{lang}: {count} repositories' for lang,count in languages.most_common())+'. Repository counts, not code bytes or proficiency.',body)
    assets=ROOT/'assets';assets.mkdir(exist_ok=True)
    # All network reads and rendering finish before any existing asset is replaced.
    for name,value in [('activity.svg',overview),('languages.svg',mix),('profile-snapshot.json',json.dumps({'updated_utc':datetime.now(timezone.utc).isoformat(),'user':USER,'public_repos':profile['public_repos'],'original_public_repos':len(originals),'followers':profile['followers'],'primary_language_repo_counts':dict(languages)},indent=2))]:
        target=assets/name;temporary=target.with_suffix(target.suffix+'.tmp')
        temporary.write_text(value,encoding='utf-8');temporary.replace(target)
    print('Updated two local SVG cards from public GitHub data; no third-party stats service required.')

if __name__=='__main__':main()
