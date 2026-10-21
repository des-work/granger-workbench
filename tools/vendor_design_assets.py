#!/usr/bin/env python3
"""Restore the vault's fonts and recipe dependencies from pinned npm packages.

Run explicitly; ordinary asset commands never access the network. Each tarball
is checked against npm's integrity digest and every retained file is recorded in
assets-vault/dependencies.lock.json with its license and SHA-256. No package
installation or downloaded JavaScript execution occurs.
"""
from pathlib import Path
import argparse,base64,hashlib,io,json,sys,tarfile,urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ultrapc import assets
LIBRARIES={
 'three':('0.160.1','build/three.min.js','three.min.js'),
 'lottie-web':('5.12.2','build/player/lottie.min.js','lottie.min.js'),
 'animejs':('3.2.2','lib/anime.min.js','anime.min.js'),
 'motion':('10.18.0','dist/motion.min.js','motion.min.js'),
 'p5':('1.9.4','lib/p5.min.js','p5.min.js'),
 'roughjs':('4.6.6','bundled/rough.js','rough.js'),
 'matter-js':('0.20.0','build/matter.min.js','matter.min.js'),
 'chroma-js':('2.4.2','chroma.min.js','chroma.min.js'),
 'open-props':('1.7.16','open-props.min.css','open-props.min.css'),
 'animate.css':('4.1.1','animate.min.css','animate.min.css'),
}
def get(url):
 with urllib.request.urlopen(url,timeout=45) as r: return r.read()
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--resolve',action='store_true',help='Resolve font package versions; otherwise reuse the lock')
 args=parser.parse_args()
 dest=assets.ASSETS_DIR;dest.mkdir(exist_ok=True)
 lock_path=dest/'dependencies.lock.json'
 old=json.loads(lock_path.read_text()) if lock_path.exists() else {'packages':[]}
 pinned={p['name']:p['version'] for p in old['packages']}
 previous={p['name']:p for p in old['packages']}
 fonts={}
 for stem in assets.FONT_MAP:
  slug,weight=stem.rsplit('-',1)
  fonts.setdefault('@fontsource/'+slug,[]).append((stem,weight))
 specs=[(pkg,pinned.get(pkg) if not args.resolve else None,faces,None) for pkg,faces in fonts.items()]
 specs += [(pkg,v,[],(source,target)) for pkg,(v,source,target) in LIBRARIES.items()]
 packages=[]
 for pkg,version,faces,lib in specs:
  prev=previous.get(pkg)
  if not args.resolve and prev and prev['version']==version and all(
    (dest/f['path']).exists() and hashlib.sha256((dest/f['path']).read_bytes()).hexdigest()==f['sha256']
    for f in prev['files']):
   packages.append(prev)
   print(pkg+' '+version+' verified locally',flush=True)
   continue
  if version is None and not args.resolve:
   raise SystemExit('No locked font version. Use --resolve once to build a lock.')
  meta=json.loads(get('https://registry.npmjs.org/'+pkg.replace('/','%2f')+'/'+(version or 'latest')))
  blob=get(meta['dist']['tarball']);integrity=meta['dist']['integrity']
  algo,digest=integrity.split('-',1)
  if base64.b64encode(hashlib.new(algo,blob).digest()).decode()!=digest:
   raise ValueError('Package integrity mismatch: '+pkg)
  tar=tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz')
  files={m.name.removeprefix('package/'):m for m in tar.getmembers() if m.isfile()}
  record={'name':pkg,'version':meta['version'],'license':meta.get('license',''),
          'tarball':meta['dist']['tarball'],'integrity':integrity,'files':[]}
  def keep(member,relative):
   data=tar.extractfile(files[member]).read()
   p=dest/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
   record['files'].append({'path':str(relative),'sha256':hashlib.sha256(data).hexdigest()})
   return data
  license_names=[n for n in files if '/' not in n and n.lower().startswith(('license','ofl'))]
  if not license_names: raise ValueError('No license found: '+pkg)
  for name in license_names:
   keep(name,Path('licenses')/pkg.replace('/','-').lstrip('@')/name)
  for stem,weight in faces:
   slug=pkg.split('/')[-1]
   candidates=[f'files/{slug}-latin-{weight}-normal.woff2',f'files/{slug}-latin-ext-{weight}-normal.woff2']
   source=next((n for n in candidates if n in files),None)
   if source is None: raise ValueError('Font face missing: '+stem)
   data=keep(source,Path('fonts')/(stem+'.woff2'))
   # PIL cannot read WOFF2 directly. Save a desktop-readable copy as well.
   from fontTools.ttLib import TTFont
   font=TTFont(io.BytesIO(data));font.flavor=None
   buf=io.BytesIO();font.save(buf);ttf=buf.getvalue();font.close()
   p=dest/'fonts'/(stem+'.ttf');p.write_bytes(ttf)
   record['files'].append({'path':str(p.relative_to(dest)),'sha256':hashlib.sha256(ttf).hexdigest()})
  if lib:
   source,target=lib
   if source not in files:
    raise ValueError('Library file missing: '+pkg+'; candidates: '+str([n for n in files if 'dist/' in n][:25]))
   keep(source,Path('libraries')/target)
  packages.append(record)
  lock_path.write_text(json.dumps({'schema':1,'packages':packages},indent=2)+'\n')
  print(pkg+' '+meta['version'],flush=True)
 lock_path.write_text(json.dumps({'schema':1,'packages':packages},indent=2)+'\n')
 print('Saved verified dependencies and licenses to',dest)
if __name__=='__main__':main()
