"""Resolve a trusted repository owner's paper inbox; no arbitrary webpage scraping."""
import argparse
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit, unquote, quote, urlencode
import update as u

def split_links(text):
    # Split whitespace only: commas may legitimately appear in DOI suffixes.
    lines = [line for line in text.splitlines() if not line.lstrip().startswith('#')]
    return list(dict.fromkeys(' '.join(lines).split()))

def identify(link):
    if re.fullmatch(r'10\.\d{4,9}/\S+', link, re.I):
        return 'doi', link.lower()
    p = urlsplit(link)
    if p.scheme not in ('http','https') or p.username or p.password:
        raise ValueError('请使用 arXiv、PubMed、DOI 链接或 DOI 编号')
    host = p.netloc.lower()
    path = unquote(p.path).rstrip('/')
    if host in ('arxiv.org','www.arxiv.org','export.arxiv.org'):
        match = re.fullmatch(r'/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?|[a-zA-Z.-]+/\d{7}(?:v\d+)?)(?:\.pdf)?', path)
        if match: return 'arxiv', re.sub(r'v\d+$','',match[1])
    if host == 'pubmed.ncbi.nlm.nih.gov' and re.fullmatch(r'/\d+',path):
        return 'pubmed', path[1:]
    if host in ('doi.org','dx.doi.org') and re.fullmatch(r'/10\.\d{4,9}/\S+',path,re.I):
        return 'doi',path[1:].lower()
    raise ValueError('暂不支持此链接；请从论文页面复制 DOI、arXiv 或 PubMed 链接')

def resolve(link):
    kind, key = identify(link)
    source = {'id':'manual-'+kind,'type':kind,'kind':'paper','name':{'doi':'Crossref','arxiv':'arXiv','pubmed':'PubMed'}[kind]}
    if kind == 'arxiv':
        records = u.parse_feed(u.fetch('https://export.arxiv.org/api/query?'+urlencode({'id_list':key})),source)
        if not records: raise ValueError('arXiv 未返回论文')
        raw = records[0]
    elif kind == 'pubmed':
        params={'db':'pubmed','id':key,'retmode':'xml','tool':'biosignal_daily'}
        if os.getenv('NCBI_API_KEY'):params['api_key']=os.environ['NCBI_API_KEY']
        if os.getenv('NCBI_EMAIL'):params['email']=os.environ['NCBI_EMAIL']
        records=u.parse_pubmed(u.fetch('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'+urlencode(params)))
        if not records:raise ValueError('PubMed 未返回论文')
        raw=records[0]
    else:
        result=json.loads(u.fetch('https://api.crossref.org/works/'+quote(key,safe='')))
        record=result['message']
        parts=record.get('published',{}).get('date-parts',[[]])[0]
        published='-'.join(str(v) if n==0 else f'{v:02d}' for n,v in enumerate(parts))
        raw={'title':(record.get('title') or [''])[0],'summary':u.clean(record.get('abstract','')),
             'doi':record.get('DOI',key),'url':'https://doi.org/'+key,'published':published}
    if not raw.get('title'):raise ValueError('没有可用标题，尚未发布')
    return raw,source

def run(inbox, data_dir, links='', limit=40):
    now=datetime.now(timezone.utc)
    day=now.astimezone(timezone(timedelta(hours=8))).date().isoformat()
    original=inbox.read_text(encoding='utf-8') if inbox.exists() else ''
    if not inbox.exists():
        inbox.parent.mkdir(parents=True,exist_ok=True)
        inbox.write_text('# 每行一个论文链接\n',encoding='utf-8')
    additions=[v for v in split_links(links) if v not in split_links(original)]
    if additions:
        inbox.parent.mkdir(parents=True,exist_ok=True)
        inbox.write_text(original.rstrip()+'\n'+'\n'.join(additions)+'\n',encoding='utf-8')
    queue=split_links(original+'\n'+links)
    if not queue:
        print('No paper links in inbox.');return 0
    index_path=data_dir/'index.json'
    index=json.loads(index_path.read_text(encoding='utf-8')) if index_path.exists() else {'schemaVersion':1,'lastRun':None,'status':'ok','sources':[],'days':[]}
    days=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((data_dir/'archive').glob('*.json'))]
    days=[d for d in days if not d.get('demo')]
    items=[i for d in days for i in d['items']]
    seen={i['id']:i for i in items}
    urls={u.canonical_url(i['url']):i for i in items}
    titles={re.sub(r'\W+','',i['title']).casefold():i for i in items}
    report_path=data_dir/'imports.json'
    old=json.loads(report_path.read_text(encoding='utf-8')).get('entries',[]) if report_path.exists() else []
    history={e['input']:e for e in old}
    # New and queued links get a turn before repeated failures.
    queue.sort(key=lambda link:history.get(link,{}).get('status')=='failed')
    entries=[];added=0;attempted=0;changed=False
    current=next((d for d in days if d['date']==day),None)
    for link in queue:
        previous=history.get(link)
        if previous and previous.get('itemId') in seen:
            entries.append(previous);continue
        entry={'input':link,'checkedAt':now.isoformat()}
        if attempted>=limit:
            entries.append({**entry,'status':'queued','message':'等待下次运行（每次最多处理 40 条）'});continue
        attempted+=1
        try:
            raw,source=resolve(link)
            item=u.normalize(raw,source,day)
            title_key=re.sub(r'\W+','',item['title']).casefold()
            duplicate=seen.get(item['id']) or urls.get(item['url']) or titles.get(title_key)
            if duplicate:
                entry.update(status='duplicate',itemId=duplicate['id'],message='已收录，未重复添加')
            else:
                u.translate(item)
                item['classification']='keywords' if item['tags'] else 'pending'
                if not item['tags']: item['tags']=['待分类']
                if current is None:
                    current={'date':day,'items':[]};days.append(current)
                current['items'].append(item);seen[item['id']]=item;urls[item['url']]=item;titles[title_key]=item
                entry.update(status='imported',itemId=item['id'],tags=item['tags'],message='已收录')
                added+=1;changed=True
        except ValueError as exc:
            # Parser/JSON errors can include source text; don't publish arbitrary responses.
            message=str(exc) if type(exc) is ValueError and str(exc).startswith(('请使用','暂不支持','arXiv','PubMed','没有可用')) else '元数据格式错误，请核对链接'
            entry.update(status='failed',message=message)
        except Exception as exc:
            entry.update(status='failed',message=f'读取失败（{type(exc).__name__}），下次运行会重试')
        entries.append(entry)
        time.sleep(3)
    if changed:
        current['items'].sort(key=lambda i:(i.get('published',''),i['id']),reverse=True)
        u.write_json(data_dir/'archive'/f'{day}.json',current)
        index['days']=sorted(days,key=lambda d:d['date'],reverse=True)
    # Don't overwrite crawler status: manual import and daily collection are independent.
    index['lastImport']=now.isoformat()
    u.write_json(index_path,index)
    report={'lastRun':now.isoformat(),'added':added,'entries':entries}
    u.write_json(report_path,report)
    counts={state:sum(e['status']==state for e in entries) for state in ('imported','duplicate','failed','queued')}
    print(json.dumps({'addedThisRun':added,**counts},ensure_ascii=False))
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:
            f.write(f'## 论文导入\n本次新增 {added}；失败 {counts["failed"]}；排队 {counts["queued"]}。\n逐条结果见网站“添加论文”或 public/data/imports.json。\n')
    return 1 if counts['failed'] else 0

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--inbox',type=Path,default=u.ROOT/'config/papers.txt')
    parser.add_argument('--data-dir',type=Path,default=u.ROOT/'public/data')
    args=parser.parse_args()
    raise SystemExit(run(args.inbox,args.data_dir,os.getenv('PAPER_LINKS','')))
