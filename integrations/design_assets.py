#!/usr/bin/env python3
"""Ultra-PC design lookup and portable export over local MCP stdio.

No model, network request, download or generated theme is used for lookup.
Only explicit export calls write files, through the vault's existing assembler.
"""
from __future__ import annotations
import argparse
import contextlib
import io
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
POLICY = ('Use the user\'s local Ultra-PC vault for UI, frontend, website, desktop, CLI and visual-design aesthetics. '
          'Choose a profile, composition and reusable asset IDs; preserve established project identity. '
          'Reuse local CSS, SVG, fonts and motion rather than inventing a theme or pasting full implementations into prompts. '
          'When the vault or a required asset is unavailable, report it and ask before using an outside aesthetic. '
          'Only claim an export after design_export succeeds; exporting is separate from opening, serving or publishing.')

class DesignError(ValueError):
    pass


def vault():
    if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
    try:
        from ultrapc import assets, webassets
    except (ImportError,SyntaxError) as exc:
        raise DesignError('Ultra-PC design source unavailable: '+str(exc)) from exc
    for path in ('DESIGN-SYSTEM.md','web/STYLE-INDEX.md','web/MODEL-INDEX.md','manifest.json'):
        if not (assets.ASSETS_DIR/path).is_file():
            raise DesignError('Ultra-PC design vault unavailable: '+str(assets.ASSETS_DIR/path)+'. Restore it before choosing an outside aesthetic.')
    return assets,webassets


def normalized(value):
    return re.sub(r'[^a-z0-9]+',' ',str(value).lower()).strip()


def _pack_for(style,w):
    return next((key for key,p in w.PACKS.items() if p['style']==style),None)


def _style_record(style,a,w):
    result=w.style_context(style)
    p=a.profile_for(style)
    # Sources and narrative briefs remain available by path, outside every prompt.
    result.pop('sources',None);result.pop('guidance',None)
    result['palette']=p['palette']
    result['fonts']={k:v for k,v in p['fonts'].items() if k!='files'}
    result['colors']={k:a.STYLES[style]['tokens'][k] for k in ('bg','text','accent')}
    result['rules']=p['rules']
    result['pack']=_pack_for(style,w)
    result['id_format']='Use style, layout and art values exactly as returned. Do not add layout/ or art/ prefixes. Only asset_id lookup uses style/, shape/ or web/. Export arguments take plain IDs, not CSS file paths.'
    if result['pack']:
        result['build']=[sys.executable,str(ROOT/'ultra.py'),'assets','web','build',result['pack'],'<empty-output-directory>']
    if p.get('modes'):result['modes']=list(p['modes'])
    if style=='nordic' and result['pack']=='nordic-daylight':
        result['application_default_palette']=p['palette']
        result['palette']='nordic-daylight';result['mode']='daylight'
        result['colors']={k:p['modes']['daylight'][k] for k in ('bg','text','accent')}
    return result


STOP={'a','an','and','are','as','at','be','build','can','could','create','design','do','for','from','give','how','i','in','is','it','like','look','looking','make','me','modern','my','of','on','or','please','should','show','some','style','styles','that','the','these','this','to','ultra','use','using','want','website','websites','what','when','which','with','would','you','your'}
GENERIC=re.compile(r'\b(design|website|web page|webpage|frontend|front end|interface|dashboard|ui|ux|landing page|aesthetic|theme|layout|assets?|vibe cod\w*)\b',re.I)


def lookup(query='',asset_id='',limit=3):
    a,w=vault()
    if isinstance(limit,bool) or not isinstance(limit,int) or not 1<=limit<=4:raise DesignError('limit must be 1 to 4')
    if not isinstance(query,str) or len(query)>4000:raise DesignError('query must be text of at most 4000 characters')
    if not isinstance(asset_id,str):raise DesignError('asset_id must be text')
    result=dict(status='ok',vault=str(a.ASSETS_DIR),policy=POLICY,
                indexes=['web/STYLE-INDEX.md','web/MODEL-INDEX.md'],counts={'styles':len(a.STYLES),'web_modules':len(w.ASSETS),'page_packs':len(w.PACKS)},styles=[],packs=[],effects=[])
    if asset_id:
        if asset_id.startswith('style/'):
            key=asset_id[6:]
            if key not in w.STYLE_DESIGNS:raise DesignError('Unknown local style: '+key)
            result['styles']=[_style_record(key,a,w)]
        elif asset_id.startswith('shape/'):
            key=asset_id[6:]
            if key not in a.SHAPES:raise DesignError('Unknown local shape: '+key)
            result['asset']=dict(id=key,profile=a.SHAPES[key]['profile'],path='shapes/'+key+'.svg')
        elif asset_id.removeprefix('web/') in w.ASSETS:
            result['effects']=[w.compact(asset_id.removeprefix('web/'))]
        elif asset_id in w.PACKS:
            result['packs']=[w.context(asset_id)]
        else:raise DesignError('Unknown local asset ID. Use style/<id>, shape/<id>, web/<id>, or a page-pack ID.')
        return result
    text=normalized(query);words=set(text.split())-STOP
    named=[key for key in w.STYLE_DESIGNS if ' '+normalized(key)+' ' in ' '+text+' ' or ' '+normalized(a.STYLES[key]['label'])+' ' in ' '+text+' ']
    # Speech uses both "high fashion" and "high-fashion"; normalized aliases
    # also match "dark academia", "art nouveau", "frutiger aero", and so on.
    if named:
        selected=named[:limit];result['selection']='named_profiles'
    else:
        scored=[]
        for key,d in w.STYLE_DESIGNS.items():
            p=a.profile_for(key)
            hay=set(normalized(key+' '+d['recognition']+' '+p['vibe']+' '+p['space']).split())
            score=len(words&hay)
            if score:scored.append((score,key))
        selected=[k for _,k in sorted(scored,key=lambda x:-x[0])[:limit]]
        result['selection']='matching_local_profiles'
        if not selected and (not text or GENERIC.search(query)):
            selected=['ultraviolet','nordic','high-fashion'][:limit]
            result['selection']='local_starting_points'
    result['styles']=[_style_record(key,a,w) for key in selected]
    # Return only requested effects; never include all implementation source.
    candidates=[]
    effect_intent=bool(words&{'effects','effect','motion','animate','animated','animations','animation','scroll','blur','transparent','transparency','glass','gradient','gradients','shader','glow','aurora','prism','iridescent','tilt','magnetic','reveal','lightbox','tabs','hover','progress'})
    for key,v in w.ASSETS.items():
        if not effect_intent:break
        if v['category']=='layout':continue
        hay=set(normalized(key+' '+v['category']+' '+v['description']+' '+' '.join(v['flags'])).split())
        score=len(words&hay)
        if score and (not named or not w.compatible(named[0],key)):
            candidates.append((score,key))
    result['effects']=[w.compact(k) for _,k in sorted(candidates,key=lambda x:-x[0])[:limit]]
    result['packs']=[{'id':k,'style':p['style'],'layout':p['layout']} for k,p in w.PACKS.items() if ' '+normalized(k)+' ' in ' '+text+' '][:limit]
    if not any((result['styles'],result['effects'],result['packs'])):result['status']='no_matches'
    return result


def export(pack,destination,style=None,layout=None,effects=None):
    a,w=vault()
    if not isinstance(pack,str) or pack not in w.PACKS:raise DesignError('Choose a page-pack ID returned by design_assets')
    if not isinstance(destination,str) or not destination.strip():raise DesignError('An explicit empty destination directory is required')
    out=Path(destination).expanduser()
    if not out.is_absolute():raise DesignError('Use an absolute destination path so the output location is explicit')
    if effects is not None and (not isinstance(effects,list) or not all(isinstance(k,str) for k in effects)):
        raise DesignError('effects must be an array of local effect IDs')
    # The existing assembler validates compatibility and settings before writing,
    # copies local fonts/licenses, and refuses a nonempty destination.
    p=w.build(pack,out,style=style,layout=layout,effects=effects)
    return dict(status='created',output=str(out.resolve()),index=str(out.resolve()/'index.html'),
                profile=p['style'],layout=p['layout'],effects=list(p['effects']),
                brief=str(out.resolve()/'AI-BRIEF.md'),design=str(out.resolve()/'design.json'),
                served=False,published=False)


TOOLS=[
 {'name':'design_assets','description':'Find the user\'s local Ultra-PC aesthetic profiles, layouts, original art, fonts, motion and page packs. Use for design/UI/frontend/website/theme requests. Returns compact IDs and file paths, not implementation source. Preserve project identity; report unavailable assets before choosing outside aesthetics.',
  'annotations':{'readOnlyHint':True,'openWorldHint':False},
  'inputSchema':{'type':'object','properties':{'query':{'type':'string'},'asset_id':{'type':'string','description':'Exact ID: style/nordic, shape/reading-room, web/glass-panel, or candlelit-library'},'limit':{'type':'integer','minimum':1,'maximum':4,'default':3}},'additionalProperties':False}},
 {'name':'design_export','description':'Assemble a requested local website from an Ultra-PC page pack into an explicit empty absolute directory. Copies selected code, fonts, art and licenses locally. Refuses existing work; does not open, serve or publish. Use only when the user asks to create/export a site.',
  'annotations':{'readOnlyHint':False,'destructiveHint':False,'openWorldHint':False},
  'inputSchema':{'type':'object','properties':{'pack':{'type':'string'},'destination':{'type':'string'},'style':{'type':'string'},'layout':{'type':'string'},'effects':{'type':'array','items':{'type':'string'}}},'required':['pack','destination'],'additionalProperties':False}}
]


def rpc(message):
    method=message.get('method');params=message.get('params') or {}
    if method=='initialize':
        return {'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'ultra-design','version':'1.0'},'instructions':POLICY}
    if method=='ping':return {}
    if method=='tools/list':return {'tools':TOOLS}
    if method=='tools/call':
        try:
            arguments=params.get('arguments') or {}
            if not isinstance(arguments,dict):raise DesignError('arguments must be an object')
            if params.get('name')=='design_assets':result=lookup(**arguments)
            elif params.get('name')=='design_export':result=export(**arguments)
            else:raise DesignError('Unknown tool')
            return {'content':[{'type':'text','text':json.dumps(result,separators=(',',':'))}]}
        except (ValueError,TypeError,KeyError,OSError) as exc:
            return {'isError':True,'content':[{'type':'text','text':json.dumps({'status':'unavailable' if 'unavailable' in str(exc) else 'error','error':str(exc)},separators=(',',':'))}]}
    return None


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--context');args=parser.parse_args(argv)
    if args.check or args.context is not None:
        try:
            if args.check:
                a,w=vault();result=dict(status='ok',root=str(a.ASSETS_DIR),styles=len(a.STYLES),effects=len(w.ASSETS),packs=len(w.PACKS),tools=[t['name'] for t in TOOLS])
            else:result=lookup(args.context,limit=2)
            print(json.dumps(result,separators=(',',':')));return 0
        except (ValueError,OSError) as exc:
            print(json.dumps({'status':'unavailable','error':str(exc)},separators=(',',':')));return 1
    for line in sys.stdin:
        try:
            message=json.loads(line)
            if not isinstance(message,dict):raise ValueError('JSON-RPC message must be an object')
            # stdout is exclusively JSON-RPC, including during portable export.
            with contextlib.redirect_stdout(io.StringIO()):result=rpc(message)
            if 'id' not in message:continue
            reply={'jsonrpc':'2.0','id':message['id']}
            if result is None:reply['error']={'code':-32601,'message':'Method not found'}
            else:reply['result']=result
            print(json.dumps(reply,separators=(',',':')),flush=True)
        except (ValueError,TypeError) as exc:
            print(json.dumps({'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':str(exc)}}),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
