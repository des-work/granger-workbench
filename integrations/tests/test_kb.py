import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hermes_kb as kb
from verify_live import verify_evidence


class KBTests(unittest.TestCase):
    def test_live_response_retains_all_five_hits(self):
        page = Path(__file__).with_name('fixtures').joinpath('kiwix-search.html').read_text()
        entries = {name: '' for name in ('devdocs_en_git_2026-04',
                   'unix.stackexchange.com_en_all_2026-02', 'superuser.com_en_all_2026-02')}
        article_html = '<html><body><p>Actual fetched article text, distinct from the search preview.</p></body></html>'
        with patch.object(kb, 'ready', return_value=entries), patch.object(kb, 'request', side_effect=[page, article_html]) as http:
            result = kb.search('git rebase')
        hits = result['hits']
        self.assertEqual(len(hits), 5)
        self.assertEqual(hits[0]['title'], 'git rebase')
        self.assertEqual(hits[0]['path'], 'git-rebase')
        self.assertIn('Reapply commits', hits[0]['snippet'])
        self.assertEqual(hits[0]['url'], kb.BASE + '/content/devdocs_en_git_2026-04/git-rebase')
        self.assertEqual(result['article']['passage'], 'Actual fetched article text, distinct from the search preview.')
        self.assertEqual(result['article']['url'], hits[0]['url'])
        self.assertEqual(http.call_args_list[1].args[0], '/content/devdocs_en_git_2026-04/git-rebase')

    def test_failed_article_fetch_does_not_fall_back_to_snippet(self):
        page = '<li><a href="/content/git/page">Git</a><cite>Preview only</cite></li>'
        with patch.object(kb, 'ready', return_value={'git': ''}), patch.object(kb, 'request', side_effect=[page, kb.KBError('Article unavailable')]):
            result = kb.rpc({'method': 'tools/call', 'params': {'name': 'kb_search', 'arguments': {'query': 'git'}}})
        self.assertTrue(result['isError'])
        self.assertIn('Article unavailable', result['content'][0]['text'])

    def test_verifier_rejects_preview_only_answer(self):
        article = {'url': kb.BASE + '/content/git/page', 'passage': 'Actual article text'}
        preview = {'hits': [{'url': article['url'], 'snippet': article['passage']}]}
        with self.assertRaisesRegex(RuntimeError, 'search previews are insufficient'):
            verify_evidence([('kb_search', json.dumps(preview))], article)

    def test_verifier_accepts_real_passage_in_hermes_envelope(self):
        article = {'url': kb.BASE + '/content/git/page', 'passage': 'Actual article text'}
        def envelope(result):
            return '<untrusted_tool_result>\nDATA\n' + json.dumps({'result': json.dumps(result)}) + '\n</untrusted_tool_result>'
        calls = [('mcp__local_kiwix_kb__kb_search', envelope({'article': article})),
                 ('mcp__local_kiwix_kb__kb_search', envelope({'query': 'zzzxqv-928371-unfindable', 'status': 'no_results', 'hits': []}))]
        verify_evidence(calls, article)
        with self.assertRaisesRegex(RuntimeError, 'actual article passage'):
            verify_evidence(calls, dict(article, passage='Different expected text'))

    def test_catalog_name_is_not_content_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'git_2026-04.zim').touch()
            library = root / 'library.xml'
            library.write_text('<library><book name="git" path="git_2026-04.zim"/></library>')
            with patch.object(kb, 'VAULT', root), patch.object(kb, 'LIBRARY', library), patch.object(kb.os.path, 'ismount', return_value=True):
                self.assertEqual(kb.books(), {'git_2026-04': 'git_2026-04.zim'})

    def test_unmounted_vault_is_a_tool_error_before_http(self):
        with patch.object(kb.os.path, 'ismount', return_value=False), patch.object(kb, 'request') as http:
            result = kb.rpc({'method': 'tools/call', 'params': {'name': 'kb_search', 'arguments': {'query': 'git'}}})
        self.assertTrue(result['isError'])
        self.assertIn('not mounted', result['content'][0]['text'])
        http.assert_not_called()

    def test_empty_results(self):
        with patch.object(kb, 'ready', return_value={'git': ''}), patch.object(kb, 'request', return_value='<html><div class="results"><ul></ul></div></html>'):
            self.assertEqual(kb.search('unfindable')['status'], 'no_results')

    def test_unknown_book_does_not_masquerade_as_no_results(self):
        with patch.object(kb, 'ready', return_value={'git': ''}), patch.object(kb, 'request', return_value='<li><a href="/content/unknown/page">A page</a></li>'):
            with self.assertRaisesRegex(kb.KBError, 'unregistered book'):
                kb.search('page')


if __name__ == '__main__':
    unittest.main()
