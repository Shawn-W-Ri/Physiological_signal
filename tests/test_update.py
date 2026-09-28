import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timezone

spec=importlib.util.spec_from_file_location('update',Path(__file__).resolve().parents[1]/'scripts/update.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
SOURCE={'id':'test','name':'Test','kind':'paper','type':'rss'}
ITEM={'title':'ECG and EEG wearable signals','summary':'A sleep and respiration study.','url':'https://example.org/paper?utm_source=rss','published':'2026-09-28'}

class CollectorTests(unittest.TestCase):
    def test_rss_atom_and_html(self):
        rss='<rss><channel><item><title>ECG &amp; PPG</title><link>https://example.org/1</link><description>&lt;b&gt;Study&lt;/b&gt;</description><pubDate>Mon, 28 Sep 2026 07:00:00 GMT</pubDate></item></channel></rss>'
        item=u.parse_feed(rss,SOURCE)[0]
        self.assertEqual(item['title'],'ECG & PPG');self.assertEqual(item['summary'],'Study');self.assertEqual(item['published'],'2026-09-28')
        atom='<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>EEG</title><link href="https://arxiv.org/abs/2609.00001v2"/><summary>Study</summary><published>2026-09-27T00:00:00Z</published></entry></feed>'
        self.assertEqual(u.parse_feed(atom,SOURCE)[0]['published'],'2026-09-27')
        parser=u.Links();parser.feed('<a href="/news/a">Wearable <b>sensor</b></a>')
        self.assertEqual(parser.items,[('/news/a','Wearable sensor')])
        with self.assertRaises(ValueError):u.parse_feed('<html/>',SOURCE)

    def test_pubmed_nested_title_and_partial_date(self):
        raw='<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>An <i>EEG</i> study</ArticleTitle><Journal><JournalIssue><PubDate><Year>2026</Year><Month>Sep</Month></PubDate></JournalIssue></Journal><Abstract><AbstractText>First.</AbstractText><AbstractText>Second.</AbstractText></Abstract></Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">10.1/ABC</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>'
        item=u.parse_pubmed(raw)[0]
        self.assertEqual(item['title'],'An EEG study');self.assertEqual(item['published'],'2026-09');self.assertEqual(item['doi'],'10.1/abc');self.assertEqual(item['summary'],'First. Second.')

    def test_tagging_and_stable_ids(self):
        item=u.normalize(ITEM,SOURCE,'2026-09-28')
        self.assertEqual(set(item['tags']),{'ECG/心电','EEG/脑电','睡眠','呼吸','可穿戴设备'})
        self.assertEqual(u.canonical_url('http://export.arxiv.org/abs/2609.00001v2'),'https://arxiv.org/abs/2609.00001')
        self.assertEqual(item['id'],u.normalize({**ITEM,'url':'https://example.org/paper'},SOURCE,'2026-09-29')['id'])
        with self.assertRaises(ValueError):u.canonical_url('javascript:alert(1)')
        self.assertIsNone(u.normalize({'title':'General news','url':'https://example.org'}, {**SOURCE,'filterByTopics':True},'2026-09-28'))

    def test_archives_idempotency_failure_and_demo_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cfg=root/'sources.json';data=root/'data'
            cfg.write_text(json.dumps({'sources':[SOURCE], 'maxItemsPerSource':10,'lookbackDays':7,'translationLimit':0}))
            u.write_json(data/'archive/2026-09-27.json',{'date':'2026-09-27','demo':True,'items':[]})
            now=datetime(2026,9,28,6,tzinfo=timezone.utc)
            with patch.object(u,'collect',return_value=[ITEM]),patch.object(u.time,'sleep'):
                self.assertEqual(u.run(cfg,data,now),0);u.run(cfg,data,now)
                index=json.loads((data/'index.json').read_text(encoding='utf-8'))
                self.assertEqual(len(index['days']),1);self.assertEqual(len(index['days'][0]['items']),1)
                self.assertFalse((data/'archive/2026-09-27.json').exists())
            archive=(data/'archive/2026-09-28.json').read_bytes()
            with patch.object(u,'collect',side_effect=TimeoutError),patch.object(u.time,'sleep'):
                self.assertEqual(u.run(cfg,data,now),1)
            self.assertEqual(archive,(data/'archive/2026-09-28.json').read_bytes())
            self.assertEqual(json.loads((data/'index.json').read_text(encoding='utf-8'))['status'],'failed')
            with patch.object(u,'collect',return_value=[ITEM]),patch.object(u.time,'sleep'):
                u.run(cfg,data,datetime(2026,9,29,6,tzinfo=timezone.utc))
            self.assertEqual(json.loads((data/'index.json').read_text(encoding='utf-8'))['days'][0]['items'],[])

    def test_translation_fallback_and_success(self):
        with patch.dict(u.os.environ,{},clear=True):
            self.assertFalse(u.translate({**ITEM}))
        env={'TRANSLATE_API_URL':'https://example.org/api','TRANSLATE_API_KEY':'test','TRANSLATE_MODEL':'test'}
        with patch.dict(u.os.environ,env,clear=True),patch.object(u,'fetch',side_effect=TimeoutError):
            self.assertFalse(u.translate({**ITEM}))
        response=json.dumps({'choices':[{'message':{'content':json.dumps({'titleZh':'心电研究','summaryZh':'研究摘要'})}}]})
        item={**ITEM}
        with patch.dict(u.os.environ,env,clear=True),patch.object(u,'fetch',return_value=response):
            self.assertTrue(u.translate(item));self.assertEqual(item['titleZh'],'心电研究')

if __name__=='__main__': unittest.main()
