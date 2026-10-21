"""Regression coverage for public-release configuration and trust boundaries."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def test_config_defaults_follow_checkout_and_explicit_overrides(tmp_path):
    code = ('from pcstudio import config; import json; '
            'print(json.dumps([str(config.ULTRA_ROOT), config.CHAT_MODEL, '
            'config.BUILD_MODEL, config.VISION_MODEL, config.OLLAMA_BASE]))')
    env = {k:v for k,v in os.environ.items() if not k.startswith('PCSTUDIO_')}
    result = subprocess.run([sys.executable,'-B','-c',code], cwd=ROOT,
                            env=env,capture_output=True,text=True,check=True)
    assert json.loads(result.stdout)[0] == str(ROOT)
    env.update(PCSTUDIO_ULTRA_ROOT=str(tmp_path),PCSTUDIO_CHAT_MODEL='chat',
               PCSTUDIO_BUILD_MODEL='planner', PCSTUDIO_VISION_MODEL='vision',
               PCSTUDIO_OLLAMA_URL='http://127.0.0.1:12345/')
    result = subprocess.run([sys.executable,'-B','-c',code], cwd=ROOT,
                            env=env,capture_output=True,text=True,check=True)
    assert json.loads(result.stdout) == [str(tmp_path),'chat','planner','vision',
                                        'http://127.0.0.1:12345']


def test_loading_reranker_preserves_http_client_verification(monkeypatch):
    from ultrapc import rerank
    class Client:
        def __init__(self, **kwargs):
            self.verify = kwargs.get('verify', True)
    original = Client.__init__
    fake_http = SimpleNamespace(Client=Client,AsyncClient=Client)
    def encoder(*args,**kwargs):
        assert fake_http.Client().verify is True
        raise OSError('certificate verification failed')
    monkeypatch.setitem(sys.modules,'httpx',fake_http)
    monkeypatch.setitem(sys.modules,'sentence_transformers',SimpleNamespace(CrossEncoder=encoder))
    monkeypatch.setitem(sys.modules,'transformers',SimpleNamespace(logging=SimpleNamespace(set_verbosity_error=lambda:None)))
    monkeypatch.setattr(rerank.core,'load_config',lambda:{})
    monkeypatch.setattr(rerank.core,'log',lambda *args:None)
    monkeypatch.setattr(rerank,'_device',lambda:'cpu')
    monkeypatch.setattr(rerank,'_MODEL',None)
    monkeypatch.setattr(rerank,'_TRIED',False)
    assert rerank.available() is False
    assert Client.__init__ is original
    assert Client().verify is True


def load_kb():
    spec = importlib.util.spec_from_file_location('release_kb',ROOT/'integrations/hermes_kb.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_explicit_kiwix_directory_does_not_require_a_mount(tmp_path,monkeypatch):
    monkeypatch.setenv('ULTRA_KIWIX_ROOT',str(tmp_path))
    (tmp_path/'example_2026.zim').touch()
    (tmp_path/'library.xml').write_text('<library><book path="example_2026.zim"/></library>')
    kb=load_kb()
    with patch.object(kb.os.path,'ismount',return_value=False):
        assert kb.books() == {'example_2026':'example_2026.zim'}
    assert kb.BASE == 'http://127.0.0.1:4386'


def test_kiwix_rejects_external_redirects(monkeypatch):
    monkeypatch.delenv('ULTRA_KIWIX_ROOT',raising=False)
    kb=load_kb()
    import pytest
    with pytest.raises(kb.KBError,match='non-local redirect'):
        kb.LocalRedirects().redirect_request(None,None,302,'',{},'https://example.com/article')


def test_generated_vault_metadata_has_no_author_checkout_paths():
    from ultrapc import assets, webassets
    catalog = assets.CATALOG.read_text() if hasattr(assets, 'CATALOG') else (assets.ASSETS_DIR/'DESIGN-SYSTEM.md').read_text()
    assert str(ROOT) not in catalog
    manifest = json.loads(assets.MANIFEST.read_text())
    assert manifest['root'] == 'assets-vault'
    gallery = (assets.ASSETS_DIR/'web/index.html').read_text()
    assert str(ROOT) not in gallery
    assert webassets.context('luminous-product', portable=True)['assemble'][1] == 'ultra.py'
    assert Path(webassets.context('luminous-product')['local_root']).is_absolute()
