"""Contract checks for portable modern web assets and small model handoffs."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ultrapc import assets,webassets as web

class LocalFiles(HTMLParser):
    def __init__(self):super().__init__();self.refs=[];self.ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        for key in ('src','href'):
            if a.get(key) and not a[key].startswith(('#','data:')):self.refs.append(a[key])


def test_packs_are_portable_and_source_is_not_sent_in_the_brief(tmp_path):
    for name in web.PACKS:
        dest=tmp_path/name
        web.build(name,dest)
        p=LocalFiles();text=(dest/'index.html').read_text();p.feed(text)
        assert not re.search(r'__[A-Z_]+__',text)
        assert len(p.ids)==len(set(p.ids)),(name,'duplicate ids')
        for ref in p.refs:
            assert not ref.startswith(('http:','https:','//')),ref
            assert (dest/ref).is_file(),(name,ref)
        for css in dest.rglob('*.css'):
            for groups in re.findall(r'url\((?:"([^"\n]*)"|\'([^\'\n]*)\'|([^)]*))\)',css.read_text()):
                ref=next((v for v in groups if v), "")
                if not ref.startswith(('data:','#')):
                    assert not ref.startswith(('http:','https:','//')),ref
                    assert (css.parent/ref).exists(),(name,css,ref)
        context=json.dumps(web.context(name),separators=(',',':'))
        assert len(context.encode())<2200,(name,'brief grew past compact budget')
        assert 'function(' not in context and '@keyframes' not in context
        assert (dest/'AI-BRIEF.md').exists() and (dest/'design.json').exists()
        for item in json.loads((dest/'assets/web/manifest.json').read_text()):
            for ref in [*item['files'].values(),item['markup']]:
                assert (dest/ref).is_file(),(name,'portable metadata path',ref)
        assert list((dest/'licenses').rglob('*')),name


def test_conflicts_and_bad_settings_do_not_create_partial_exports(tmp_path):
    target=tmp_path/'forbidden'
    with pytest.raises(ValueError,match='incompatible'):
        web.build('luminous-product',target,style='swiss-international')
    assert not target.exists()
    with pytest.raises(ValueError,match='Invalid setting'):
        web.build('luminous-product',target,settings={'tilt-card':{'angle':1000}})
    assert not target.exists()
    with pytest.raises(ValueError,match='Invalid setting'):
        web.build('luminous-product',target,settings={'tilt-card':{'angle':float('nan')}})
    assert not target.exists()
    target.mkdir();(target/'my-work.txt').write_text('keep me')
    with pytest.raises(ValueError,match='empty'):
        web.build('luminous-product',target)
    assert (target/'my-work.txt').read_text()=='keep me'


def test_every_asset_has_a_working_demo_and_self_contained_sources():
    root=assets.ASSETS_DIR/'web'
    for key,v in web.ASSETS.items():
        assert v['fallback'] and v['cost'] in ('low','medium','high')
        assert (root/f'demos/{key}/index.html').exists()
        assert (root/f'effects/{key}.js').exists()
        assert (root/f'effects/{key}.css').exists()
        p=LocalFiles();p.feed((root/f'demos/{key}/index.html').read_text())
        for ref in p.refs:assert (root/f'demos/{key}'/ref).exists(),(key,ref)
        assert not re.search(r'\b(?:fetch|XMLHttpRequest|WebSocket)\b',v['js'])
    assert not web.audit()


def test_context_lookup_and_search_are_metadata_only(capsys):
    assert web.handle(['context','glass-command'])==0
    result=json.loads(capsys.readouterr().out)
    assert result['style']=='y2k-chrome' and 'glass-dock' in result['effects']
    assert web.handle(['search','glass','--style','swiss-international','--json'])==0
    assert not json.loads(capsys.readouterr().out)
    assert web.handle(['show','glass-panel','--code','css'])==0
    assert 'backdrop-filter' in capsys.readouterr().out


def test_browser_javascript_parses(tmp_path):
    if not shutil.which('node'):pytest.skip('Node not installed')
    for key in web.ASSETS:
        p=tmp_path/(key+'.js');p.write_text(web._js(key))
        r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
        assert r.returncode==0,(key,r.stderr)
    p=tmp_path/'runtime.js';p.write_text(web.RUNTIME_JS)
    assert subprocess.run(['node','--check',str(p)],capture_output=True).returncode==0
    gallery=(assets.ASSETS_DIR/'web/index.html').read_text()
    for i,script in enumerate(re.findall(r'<script>(.*?)</script>',gallery,re.S)):
        p=tmp_path/f'gallery-{i}.js';p.write_text(script)
        r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
        assert r.returncode==0,r.stderr


def test_runtime_mounts_deferred_modules_once_and_cleans_up(tmp_path):
    if not shutil.which('node'):pytest.skip('Node not installed')
    runtime=tmp_path/'runtime.js';runtime.write_text(web.RUNTIME_JS)
    test=tmp_path/'runtime-test.cjs'
    test.write_text(r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Node extends EventTarget{
 constructor(){super();this.dataset={uv:'probe',uvConfig:'{"distance":9999}'};this.properties=new Map();this.style={getPropertyValue:k=>this.properties.get(k)||'',setProperty:(k,v)=>this.properties.set(k,v),removeProperty:k=>this.properties.delete(k)};}
 matches(s){return s==='[data-uv]';}querySelectorAll(){return [];}contains(n){return n===this;}
}
async function run(readyState){
 const el=new Node(),doc=new EventTarget(),globalEvents=new EventTarget(),mq=new EventTarget();mq.matches=false;doc.readyState=readyState;doc.hidden=false;doc.querySelectorAll=()=>[el];doc.documentElement={hasAttribute:()=>false,toggleAttribute(){}};
 let calls=0,hits=0,clean=0;
 const ctx={document:doc,matchMedia:()=>mq,queueMicrotask,requestAnimationFrame:()=>0,cancelAnimationFrame(){},console,addEventListener:globalEvents.addEventListener.bind(globalEvents)};ctx.window=ctx;vm.createContext(ctx);vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),ctx);
 ctx.UltraWeb.register('probe',{distance:{default:20,min:0,max:80,unit:'px',css:'--test'}},(node,o,api)=>{calls++;assert.equal(o.distance,80);api.listen(node,'click',()=>hits++);api.clean(()=>clean++);});
 if(readyState==='loading')doc.dispatchEvent(new Event('DOMContentLoaded'));await Promise.resolve();
 assert.equal(calls,1,'deferred registration failed to mount');
 for(let i=0;i<10;i++)ctx.UltraWeb.mount();el.dispatchEvent(new Event('click'));assert.equal(hits,1);assert.equal(calls,1);
 assert.equal(el.style.getPropertyValue('--test'),'80px');ctx.UltraWeb.unmount();assert.equal(clean,1);assert.equal(el.style.getPropertyValue('--test'),'');
 el.dispatchEvent(new Event('click'));assert.equal(hits,1,'listener leaked after unmount');assert.equal(ctx.UltraWeb.stats().instances,0);
 ctx.UltraWeb.mount();el.dispatchEvent(new Event('click'));assert.equal(hits,2);ctx.UltraWeb.unmount();assert.equal(clean,2);
}
(async()=>{for(const state of ['loading','interactive','complete'])await run(state);console.log('runtime lifecycle passed');})().catch(e=>{console.error(e);process.exit(1);});
''')
    result=subprocess.run(['node',str(test),str(runtime)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
