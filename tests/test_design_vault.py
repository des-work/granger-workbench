"""Regression checks for profile fidelity, portability, and usable controls."""
from pathlib import Path
import hashlib
import json
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ultrapc import assets, nativeui as nui


def test_secondary_text_is_readable_on_real_surfaces():
    for style,desc in assets.STYLES.items():
        t=desc['tokens']
        for surface in ('bg','bg2','surface'):
            assert nui.contrast(t['text'],t[surface]) >= 4.5,(style,surface,'body')
            assert nui.contrast(t['muted'],t[surface]) >= 4.5,(style,surface,'secondary')
        ink=nui.on_color(t['accent'])
        assert nui.contrast(ink,t['accent']) >= 4.5,(style,'button')


def test_starters_obey_profiles_and_survive_a_rerun(tmp_path):
    for style,e in assets.EXEC.items():
        out=tmp_path/style
        assert assets.cmd_scaffold(str(out),style)==0
        css=(out/'styles.css').read_text()
        html=(out/'index.html').read_text()
        if 'gradient' in e['forbid']:
            assert not assets._gradient_violations(css),style
        if 'glass' in e['forbid']:
            assert not re.search(r'backdrop-filter:\s*blur',css),style
        if 'shadow' in e['forbid']:
            assert not assets._shadow_violations(css,'shadow'),style
        assert 'prefers-reduced-motion: reduce' in css
        assert ':focus-visible' in css
        assert (out/'fonts/fonts.css').exists()
        assert not re.search(r'(?:src|href)=[\"\']https?://',html)
        (out/'index.html').write_text('my work')
        assert assets.cmd_scaffold(str(out),style)==2
        assert (out/'index.html').read_text()=='my work'


def test_native_flat_styles_do_not_inherit_aero_materials():
    for style in ('swiss-international','mono','hi-contrast','mosaic','avant-basic'):
        button=nui.gel_button(160,44,style)
        assert button.getpixel((80,12))==button.getpixel((80,30)),style
        header=nui.header_bar(320,56,style)
        assert header.getpixel((100,5))==header.getpixel((100,35)),style
    swiss=nui.glass_card(300,240,'swiss-international')
    assert swiss.getpixel((100,80))==swiss.getpixel((100,180))
    aero=nui.gel_button(160,44,'frutiger-aero')
    assert aero.getpixel((80,12))!=aero.getpixel((80,30))
    archive=nui.glass_card(300,240,'golden-archive')
    assert archive.getpixel((100,80))==archive.getpixel((100,180))


def test_small_progress_is_visible_and_values_are_bounded():
    assert nui.progress_img(200,14,.02).tobytes()!=nui.progress_img(200,14,0).tobytes()
    assert nui.progress_img(200,14,-1).tobytes()==nui.progress_img(200,14,0).tobytes()
    assert nui.progress_img(200,14,5).tobytes()==nui.progress_img(200,14,1).tobytes()


def test_dependency_inventory_and_profile_fonts_are_complete():
    lock=json.loads((assets.ASSETS_DIR/'dependencies.lock.json').read_text())
    for pkg in lock['packages']:
        assert pkg['license'],pkg['name']
        assert any(f['path'].startswith('licenses/') for f in pkg['files']),pkg['name']
        for entry in pkg['files']:
            p=assets.ASSETS_DIR/entry['path']
            assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],entry['path']
    for name,profile in assets.PROFILES.items():
        for f in profile['fonts']['files']:
            assert (assets.FONT_DIR/f).is_file(),(name,f)
            assert (assets.FONT_DIR/f.replace('.woff2','.ttf')).is_file(),(name,f)


def test_generated_gallery_has_no_missing_local_destinations():
    for p in (assets.DEMO,assets.SHOWCASE):
        s=p.read_text()
        for ref in re.findall(r'(?:src|href)=["\']([^"\']+)',s):
            if not ref.startswith(('#','http:','https:','data:')):
                assert (p.parent/ref).exists(),(p.name,ref)
    m=json.loads(assets.MANIFEST.read_text())
    demo=assets.DEMO.read_text()
    assert f'fonts {len(m["fonts"])}' in demo
    for name in assets.STYLES:
        assert f'assets kit {name}' in demo


def test_all_kits_pass_and_gradient_corrections_reach_hero_css():
    for style in assets.STYLES:
        assert not [issue for issue in assets.check_style(style) if issue[0] in ('FAIL','WARN')],style
        css,plan=assets._kit_css(style)
        if plan['gradient']:
            wash=assets.hero_scrim(style,plan['gradient'])
            t=assets.STYLES[style]['tokens']
            if wash:
                assert 'background: linear-gradient(rgba(' in css
                assert min(assets._contrast(t['text'],assets._composite(t['bg'],stop,wash))
                           for stop in assets._gradient_stops(plan['gradient']))>=4.5,style
            else:
                fg,ratio=assets._on_gradient_fg(style,plan['gradient'])
                assert ratio>=4.5 and f'color: {fg};' in css,style


def test_resource_audit_detects_a_missing_dependency(monkeypatch):
    assert not assets.check_resources()
    real=Path.is_file
    monkeypatch.setattr(Path,'is_file',lambda p: False if p.name=='chroma.min.js' else real(p))
    assert any(level=='FAIL' and 'chroma.min.js' in detail
               for level,rule,detail in assets.check_resources())


def test_qualified_asset_ids_disambiguate_native_and_web(capsys):
    assert assets.cmd_show('native/glass-card')==0
    native=capsys.readouterr().out
    assert 'nui.Card' in native
    assert assets.cmd_show('css/glass-card')==0
    assert 'backdrop-filter' in capsys.readouterr().out
    assert assets.cmd_show('style/golden-archive')==0
    assert '--font-display' in capsys.readouterr().out
