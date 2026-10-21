"""Style recognition, named modes and offline specimen portability."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import subprocess
import shutil
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ultrapc import assets as a, webassets as w, nativeui as n

class Links(HTMLParser):
    def __init__(self):super().__init__();self.refs=[];self.ids=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        for key in ('href','src'):
            value=attrs.get(key,'')
            if value and not value.startswith(('#','data:')):self.refs.append(value)


def test_directions_cover_the_vault_without_claiming_registers_are_movements():
    assert set(w.STYLE_DESIGNS)==set(a.STYLES)
    registers={key for key,d in w.STYLE_DESIGNS.items() if d['kind']=='System / color register'}
    assert registers=={'neutral','hi-contrast','pastel','earthy','jewel','ultraviolet','ember'}
    for style in a.STYLES:
        ctx=w.style_context(style)
        assert len(json.dumps(ctx).encode())<2400
        assert ctx['art'] and ctx['recognition'] and ctx['layout'] in w.ASSETS


def test_all_style_specimens_have_local_links_and_resolved_markup():
    for style in a.STYLES:
        path=a.ASSETS_DIR/f'web/styles/{style}/index.html'
        text=path.read_text();p=Links();p.feed(text)
        assert not re.search(r'__[A-Z_]+__',text),style
        assert len(p.ids)==len(set(p.ids)),(style,'duplicate IDs')
        assert 'Designed to move.' not in text and 'Local assets. Your identity.' not in text,style
        for ref in p.refs:
            assert not ref.startswith(('http:','https:','//')),(style,ref)
            assert (path.parent/ref).is_file(),(style,ref)
        ctx=json.loads((path.parent/'context.json').read_text())
        assert ctx['style']==style
        for key in ctx['art']:assert (a.SHAPES_DIR/(key+'.svg')).is_file(),key


def test_requested_styles_have_different_compositions_and_original_scene_assets():
    focus=('dark-academia','cyberpunk','high-fashion','nordic')
    assert len({w.STYLE_DESIGNS[k]['layout'] for k in focus})==4
    assert len({a.PROFILES[k]['hero_asset'] for k in focus})==4
    for style in (*focus,'bauhaus','art-nouveau'):
        p=a.PROFILES[style]
        assert p['sources'] and any('127.0.0.1:4386' in s for s in p['sources'])
        art=a.SHAPES[p['hero_asset']]['svg'];svg=ET.fromstring(art)
        assert svg.attrib['viewBox']=='0 0 720 840'
        assert not re.search(r'(?:href|src)=[\"\'](?:https?:|//)',art)
        assert not any(el.tag.endswith(('script','image','foreignObject')) for el in svg.iter())


def test_nordic_daylight_is_explicit_and_keeps_legacy_application_colors(tmp_path):
    assert a.STYLES['nordic']['tokens']['bg']=='#2e3440'
    mode=a.PROFILES['nordic']['modes']['daylight']
    for fg in ('text','muted'):
        for bg in ('bg','bg2','surface'):assert n.contrast(mode[fg],mode[bg])>=4.5,(fg,bg)
    assert n.contrast(mode['on-accent'],mode['accent'])>=4.5
    out=tmp_path/'daylight';w.build('nordic-daylight',out)
    assert 'data-uv-mode="daylight"' in (out/'index.html').read_text()
    other=w.plan('luminous-product',style='nordic',layout='product-bento',effects=[])
    out=tmp_path/'legacy';w.build('luminous-product',out,prepared=other)
    assert 'data-uv-mode="daylight"' not in (out/'index.html').read_text()


def test_css_audit_does_not_mistake_custom_tokens_for_properties():
    css='body[data-uv-mode=daylight]{--border:#bec5ba;border:var(--border);--font-size:100px;font-size:var(--size-0);}'
    assert a._decl_values(css,'border')==[('var(--border)',1)]
    assert a._decl_values(css,'font-size')==[('var(--size-0)',1)]


def test_atlas_scripts_parse_and_all_destinations_exist(tmp_path):
    playground=(a.ASSETS_DIR/'web/index.html').read_text()
    assert f'{len(w.ASSETS)} ASSETS · {len(w.PACKS)} PAGE PACKS' in playground
    for path in (a.SHOWCASE,a.ASSETS_DIR/'web/styles/index.html'):
        text=path.read_text();p=Links();p.feed(text)
        for ref in p.refs:
            if not ref.startswith(('http:','https:')):assert (path.parent/ref).is_file(),ref
        if shutil.which('node'):
            for i,script in enumerate(re.findall(r'<script>(.*?)</script>',text,re.S)):
                out=tmp_path/f'{path.stem}-{i}.js';out.write_text(script)
                check=subprocess.run(['node','--check',str(out)],capture_output=True,text=True)
                assert check.returncode==0,check.stderr
