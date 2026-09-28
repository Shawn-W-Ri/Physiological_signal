import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from support import temp_directory
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import import_papers as p

class ImportTests(unittest.TestCase):
    def test_recognized_links_and_invalid_hosts(self):
        for link,expected in [
            ('https://arxiv.org/pdf/2401.12345v2.pdf',('arxiv','2401.12345')),
            ('https://arxiv.org/abs/hep-th/9901001v2',('arxiv','hep-th/9901001')),
            ('https://pubmed.ncbi.nlm.nih.gov/123456/?x=1',('pubmed','123456')),
            ('https://doi.org/10.1234/ABC',('doi','10.1234/abc')),
            ('10.1234/ABC',('doi','10.1234/abc'))]:
            self.assertEqual(p.identify(link),expected)
        for link in ['https://arxiv.org.evil.test/abs/2401.12345','http://127.0.0.1/foo','javascript:alert(1)','https://user:pw@doi.org/10.1234/a']:
            with self.assertRaises(ValueError):p.identify(link)
        self.assertEqual(p.split_links('# comment\n10.1234/a,b\n10.1234/a,b 10.1234/c'),['10.1234/a,b','10.1234/c'])

    def test_crossref_metadata_missing_abstract(self):
        response={'message':{'title':['ECG and PPG study'],'DOI':'10.1234/test','published':{'date-parts':[[2025,2]]}}}
        with patch.object(p.u,'fetch',return_value=json.dumps(response)):
            raw,source=p.resolve('10.1234/test')
        self.assertEqual(raw['published'],'2025-02');self.assertEqual(raw['summary'],'')
        self.assertEqual(source['name'],'Crossref')

    def test_arxiv_and_pubmed_resolvers(self):
        atom='<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>EEG</title><link href="https://arxiv.org/abs/2401.12345v2"/><summary>Brain signals</summary><published>2024-01-01T00:00:00Z</published></entry></feed>'
        with patch.object(p.u,'fetch',return_value=atom):
            raw,source=p.resolve('https://arxiv.org/pdf/2401.12345.pdf')
        self.assertEqual(source['name'],'arXiv');self.assertEqual(raw['title'],'EEG')
        xml='<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>EMG study</ArticleTitle></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>'
        with patch.object(p.u,'fetch',return_value=xml):
            raw,source=p.resolve('https://pubmed.ncbi.nlm.nih.gov/123/')
        self.assertEqual(source['name'],'PubMed');self.assertEqual(raw['title'],'EMG study')

    def test_mixed_batch_multitag_pending_retry_and_idempotency(self):
        source={'id':'manual-doi','type':'doi','kind':'paper','name':'Crossref'}
        def resolve(link):
            if link.endswith('/bad'):raise TimeoutError()
            return {'title':'ECG with PPG' if link.endswith('/one') else 'Unrelated methodology','summary':'','url':'https://doi.org/'+link,'doi':link,'published':'2020'},source
        with temp_directory() as temp:
            root=Path(temp);inbox=root/'papers.txt';data=root/'data'
            p.u.write_json(data/'index.json',{'schemaVersion':1,'status':'partial','sources':[],'days':[],'lastRun':None})
            with patch.object(p,'resolve',side_effect=resolve),patch.object(p.time,'sleep'),patch.object(p.u,'translate',return_value=False):
                self.assertEqual(p.run(inbox,data,'10.1234/one 10.1234/two 10.1234/bad'),1)
                index=json.loads((data/'index.json').read_text(encoding='utf-8'))
                self.assertEqual(index['status'],'partial')
                items=index['days'][0]['items'];self.assertEqual(len(items),2)
                self.assertTrue(any(set(i['tags'])=={'ECG/心电','PPG'} for i in items))
                self.assertTrue(any(i['tags']==['待分类'] for i in items))
                before=list((data/'archive').glob('*.json'))[0].read_bytes()
                with patch.object(p,'resolve',side_effect=resolve) as call:
                    p.run(inbox,data)
                    self.assertEqual(call.call_count,1) # only failed link is retried
                self.assertEqual(before,list((data/'archive').glob('*.json'))[0].read_bytes())

    def test_new_queue_not_starved_by_failure(self):
        with temp_directory() as temp:
            root=Path(temp);data=root/'data';inbox=root/'papers.txt'
            inbox.write_text('10.1234/bad\n10.1234/new',encoding='utf-8')
            p.u.write_json(data/'imports.json',{'entries':[{'input':'10.1234/bad','status':'failed'}]})
            with patch.object(p,'resolve',side_effect=TimeoutError()) as call,patch.object(p.time,'sleep'):
                p.run(inbox,data,limit=1)
                call.assert_called_once_with('10.1234/new')

    def test_content_references(self):
        root=Path(__file__).resolve().parents[1]/'public/data'
        topics=json.loads((root/'topics.json').read_text(encoding='utf-8'))
        sensors=json.loads((root/'sensors.json').read_text(encoding='utf-8'))
        methods=json.loads((root/'methods.json').read_text(encoding='utf-8'))
        names={t['name'] for t in topics};ids={s['id'] for s in sensors}
        self.assertEqual(len(topics),8)
        for item in sensors+methods:
            self.assertTrue(set(item['tags'])<=names)
            self.assertTrue(item['url'].startswith('https://'))
        for item in methods:self.assertTrue(set(item['sensorIds'])<=ids)

if __name__=='__main__':unittest.main()
