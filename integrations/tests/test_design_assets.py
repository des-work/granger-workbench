"""Local design MCP and voice context contract checks; no microphone or model."""
import importlib.util
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

BRIDGE=Path(__file__).resolve().parents[1]/'design_assets.py'
spec=importlib.util.spec_from_file_location('design_bridge',BRIDGE)
design=importlib.util.module_from_spec(spec);spec.loader.exec_module(design)

class DesignBridgeTests(unittest.TestCase):
    def test_named_style_resolves_to_real_layout_art_and_small_context(self):
        for query,profile,layout,art in [
            ('a dark academia website','dark-academia','scholar-folio','reading-room'),
            ('a cyberpunk dashboard','cyberpunk','signal-console','night-city-feed'),
            ('a high fashion website','high-fashion','atelier-spread','couture-silhouette'),
            ('a Nordic interface','nordic','nordic-catalog','daylight-objects')]:
            result=design.lookup(query,limit=1)
            self.assertEqual(result['status'],'ok');self.assertEqual(result['selection'],'named_profiles')
            record=result['styles'][0]
            self.assertEqual((record['style'],record['layout'],record['art'][0]),(profile,layout,art))
            self.assertTrue((Path(result['vault'])/record['profile']).is_file())
            self.assertTrue((Path(result['vault'])/('shapes/'+art+'.svg')).is_file())
            self.assertLess(len(json.dumps(result)),4200)
            self.assertNotIn('@keyframes',json.dumps(result))
        self.assertEqual(record['mode'],'daylight')
        self.assertEqual(record['palette'],'nordic-daylight')
        self.assertEqual(record['application_default_palette'],'nordic-frost')

    def test_style_lookup_does_not_recommend_unrequested_effects(self):
        result=design.lookup('Which original art asset and layout suit a Nordic website?')
        self.assertEqual(result['effects'],[])
        result=design.lookup('A Nordic website with glass transparency')
        self.assertTrue(result['effects'])

    def test_missing_ids_and_vault_are_explicit(self):
        with self.assertRaises(design.DesignError):design.lookup(asset_id='style/not-a-style')
        with self.assertRaises(design.DesignError):design.lookup(asset_id='../../private')
        for value in [0,5,True,'3']:
            with self.assertRaises(design.DesignError):design.lookup('glass',limit=value)
        self.assertEqual(design.lookup('zzzxqv928371unfindable')['status'],'no_matches')
        a,w=design.vault()
        with tempfile.TemporaryDirectory() as folder,patch.object(a,'ASSETS_DIR',Path(folder)):
            with self.assertRaisesRegex(design.DesignError,'unavailable'):design.lookup('Nordic website')

    def test_profile_constraints_filter_effects(self):
        result=design.lookup('Swiss International website with glass gradients',limit=4)
        a,w=design.vault()
        self.assertEqual(result['styles'][0]['style'],'swiss-international')
        for effect in result['effects']:
            self.assertEqual(w.compatible('swiss-international',effect['id']),[])

    def test_export_is_real_offline_and_preserves_existing_work(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'site'
            result=design.export('candlelit-library',str(target))
            self.assertEqual(result['status'],'created');self.assertFalse(result['published'])
            self.assertIn('candlelit reading room',(target/'index.html').read_text())
            self.assertTrue((target/'fonts/fonts.css').is_file())
            self.assertTrue(list((target/'licenses').rglob('*')))
            old=(target/'index.html').read_bytes()
            with self.assertRaises(ValueError):design.export('candlelit-library',str(target))
            self.assertEqual((target/'index.html').read_bytes(),old)
            forbidden=Path(folder)/'invalid'
            with self.assertRaisesRegex(ValueError,'incompatible'):
                design.export('luminous-product',str(forbidden),style='swiss-international')
            self.assertFalse(forbidden.exists())
            with self.assertRaisesRegex(ValueError,'absolute'):design.export('nordic-daylight','relative-site')

    def test_protocol_discovers_calls_and_exports_without_stdout_noise(self):
        with tempfile.TemporaryDirectory() as folder:
            messages=[
             {'jsonrpc':'2.0','id':1,'method':'initialize'},
             {'jsonrpc':'2.0','method':'notifications/initialized'},
             {'jsonrpc':'2.0','id':2,'method':'tools/list'},
             {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'design_assets','arguments':{'asset_id':'style/high-fashion'}}},
             {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'design_export','arguments':{'pack':'nordic-daylight','destination':str(Path(folder)/'site')}}},
             {'jsonrpc':'2.0','id':5,'method':'tools/call','params':{'name':'design_assets','arguments':{'asset_id':'style/missing'}}}]
            process=subprocess.run([sys.executable,'-B',str(BRIDGE)],input='\n'.join(json.dumps(m) for m in messages)+'\n',capture_output=True,text=True,timeout=15)
            self.assertEqual(process.returncode,0,process.stderr)
            replies=[json.loads(line) for line in process.stdout.splitlines()]
            self.assertEqual([r['id'] for r in replies],[1,2,3,4,5])
            self.assertIn('Ultra-PC',replies[0]['result']['instructions'])
            self.assertEqual({t['name'] for t in replies[1]['result']['tools']},{'design_assets','design_export'})
            self.assertEqual(json.loads(replies[2]['result']['content'][0]['text'])['styles'][0]['style'],'high-fashion')
            self.assertEqual(json.loads(replies[3]['result']['content'][0]['text'])['status'],'created')
            self.assertTrue(replies[4]['result']['isError'])

if __name__=='__main__':unittest.main()
