import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pcstudio import animate, easy, jobs, mcp, research, workbench

class RoutingTests(unittest.TestCase):
    def test_build_types_and_subjects(self):
        for text,kind,subject in [
            ('Build me a model of a table','model','a table'),
            ('Can you build me a 3D model of a chair?','model','a chair'),
            ('make a 3D animation of a rocket','animation','a rocket'),
            ('make an animation of a cat in Blender','animation','a cat'),
            ('build a terminal animation of a ship','terminal-animation','a ship'),
            ('build me an animation','terminal-animation','')]:
            self.assertEqual(jobs.intent(text),dict(kind=kind,subject=subject))
        for text in ('what is a model','build a language model','build a model to classify images','open Blender'):
            self.assertIsNone(jobs.intent(text))

    def test_named_program_does_not_swallow_a_build(self):
        self.assertIsNone(easy._find_local_tool('build an animation of a ship in termstage',{'termstage':'exe'}))
        self.assertEqual(easy._find_local_tool('open termstage',{'termstage':'exe'}),('termstage','exe'))

    def test_registry_separates_model_and_animation(self):
        with patch.object(workbench,'_resolve',return_value=['pc']):
            self.assertEqual(workbench.find_app('build a 3D model of a table')['name'],'3D model')
            self.assertEqual(workbench.find_app('build a 3D animation of a table')['name'],'3D animation')

    def test_both_voice_entries_start_jobs_not_gui_or_model_claims(self):
        for entry in ('ask','granger'):
            request='build a 3D model of a table'
            report={'status':'queued','kind':'model','subject':'a table','job_id':'a'*32}
            transcripts=[('goodbye',None)] if entry=='granger' else [(request,None),('goodbye',None)]
            def standby(args,voice,mode,tools,voiceid):
                easy._converse(args,voice,mode,tools,voiceid,first_turn=(request,None))
            with contextlib.ExitStack() as stack:
                for target,value in [('_tts_voices',{}),('_load_voice_default',None),('_load_confirm_default','button'),('_local_tools',{'Blender':'exe'})]:
                    stack.enter_context(patch.object(easy,target,return_value=value))
                stack.enter_context(patch.object(easy.cli,'aec_available',return_value=False))
                stack.enter_context(patch.object(easy,'_record_transcript',side_effect=transcripts))
                stack.enter_context(patch.object(easy,'_confirm',return_value=True))
                stack.enter_context(patch.object(easy,'_standby',side_effect=standby))
                start=stack.enter_context(patch.object(jobs,'start',return_value=report))
                chat=stack.enter_context(patch.object(easy,'_ask_hermes_chat'))
                launch=stack.enter_context(patch.object(easy,'_launch_tool'))
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                self.assertEqual(easy.main([entry,'--no-play','--no-voice-id']),0)
                start.assert_called_once_with(kind='model',subject='a table')
                chat.assert_not_called();launch.assert_not_called()

    def test_job_followup_uses_actual_status(self):
        with patch.object(jobs,'status',return_value={'status':'failed','error':'GPU unavailable'}),patch.object(workbench,'terminal_context') as terminal:
            result=easy._prepare_question('is it done?',active_job='a'*32)
        self.assertIn('GPU unavailable',result);terminal.assert_not_called()

    def test_local_ai_questions_get_actual_capabilities_and_current_override(self):
        with patch('pcstudio.mcp.capabilities',return_value={'hermes_inference':{'chat_model':'coding-default'}}):
            result=easy._prepare_question('Which local AI model are you using?',model='voice-override')
        self.assertIn('coding-default',result);self.assertIn('voice-override',result)
        self.assertIn('configuration/dependency check',result)


    def test_hermes_command_keeps_model_session_and_spoken_constraints(self):
        result=subprocess.CompletedProcess([],0,'A grounded answer.','session_id: local-session\n')
        with patch.object(easy.shutil,'which',return_value='/hermes'),patch.object(easy.subprocess,'run',return_value=result) as run:
            answer,session=easy._ask_hermes_chat('Question',model='voice-local',session_id='previous')
        command=run.call_args.args[0]
        self.assertEqual(command[command.index('-m')+1],'voice-local')
        self.assertEqual(command[command.index('--resume')+1],'previous')
        self.assertIn('ask one clarification and stop',command[command.index('-q')+1])
        self.assertIn('spoken plain paragraphs',command[command.index('-q')+1])
        self.assertEqual((answer,session),('A grounded answer.','local-session'))


    def test_running_build_does_not_hide_machine_health_questions(self):
        with patch.object(easy,'_device_snapshot',return_value={'cpu':{'temperature':73}}),patch.object(jobs,'status') as status:
            result=easy._prepare_question('Why is my CPU running hot?',active_job='a'*32)
        self.assertIn('73',result);status.assert_not_called()


    def test_internal_template_is_retried_once_for_read_only_evidence(self):
        bad=subprocess.CompletedProcess([],0,'[OUT-OF-BAND USER MESSAGE] <their message>','session_id: first\n')
        good=subprocess.CompletedProcess([],0,'A sourced answer.','session_id: first\n')
        with patch.object(easy.shutil,'which',return_value='/hermes'),patch.object(easy.subprocess,'run',side_effect=[bad,good]) as run:
            answer,_=easy._ask_hermes_chat('Question [Local source evidence, fetched for this request: {}]',model='local',session_id=None)
        self.assertEqual(answer,'A sourced answer.');self.assertEqual(run.call_count,2)

    def test_action_turn_is_never_replayed_for_a_bad_answer(self):
        bad=subprocess.CompletedProcess([],0,'<their message>','session_id: first\n')
        with patch.object(easy.shutil,'which',return_value='/hermes'),patch.object(easy.subprocess,'run',return_value=bad) as run:
            with self.assertRaisesRegex(RuntimeError,'internal template'):
                easy._ask_hermes_chat('Build a model',model='local',session_id=None)
        self.assertEqual(run.call_count,1)


    def test_ambiguous_topic_is_clarified_without_model_fabrication(self):
        with patch.object(research,'search',return_value={'status':'ambiguous','choices':[]}):
            prompt=research.augment('Tell me about Mercury')
        with patch.object(easy.subprocess,'run') as model:
            self.assertEqual(easy._ask_hermes_chat(prompt,model='local',session_id=None),('Which meaning of Mercury do you mean?',None))
            model.assert_not_called()
        self.assertEqual(research.followup('Mercury','the planet'),'Tell me about Mercury (planet)')
        self.assertEqual(research.followup('Mercury','What is my CPU usage?'),'What is my CPU usage?')


class JobTests(unittest.TestCase):
    def test_bad_requests_do_not_launch_processes(self):
        for kwargs in [dict(kind='shell',subject='anything'),dict(kind='model',subject=''),dict(kind='animation',subject='rocket',width=129),dict(kind='animation',subject='rocket',frames=100000),dict(kind='animation',subject='rocket',template='invalid')]:
            with patch.object(jobs.subprocess,'Popen') as launch:
                with self.assertRaises(ValueError):jobs.start(**kwargs)
                launch.assert_not_called()

    def test_no_vault_no_new_aesthetic(self):
        with patch.object(jobs,'_design',side_effect=RuntimeError('vault unavailable')),patch.object(jobs.subprocess,'Popen') as launch:
            with self.assertRaisesRegex(RuntimeError,'vault unavailable'):jobs.start('model','a chair')
            launch.assert_not_called()

    def test_failed_builder_records_failure_and_never_success(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(jobs,'JOBS',Path(temp)):
            folder=Path(temp)/('a'*32);folder.mkdir()
            (folder/'job.json').write_text(json.dumps(dict(job_id='a'*32,status='queued',kind='model',subject='chair',design={},artifacts=[])))
            with patch('pcstudio.cli.model_command',side_effect=RuntimeError('bad scene')):
                jobs.run('a'*32)
            result=jobs.status('a'*32)
            self.assertEqual(result['status'],'failed');self.assertIn('bad scene',result['error'])

    def test_missing_output_invalidates_completed_job(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(jobs,'JOBS',Path(temp)):
            folder=Path(temp)/('a'*32);folder.mkdir()
            (folder/'job.json').write_text(json.dumps(dict(status='complete',artifacts=[str(folder/'missing.obj')])))
            self.assertEqual(jobs.status('a'*32)['status'],'failed')
            for ident in ('../secrets','invalid','a'*33):
                with self.assertRaises(ValueError):jobs.status(ident)

    def test_busy_does_not_start_duplicate(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(jobs,'JOBS',Path(temp)),patch.object(jobs,'_design',return_value={}):
            folder=Path(temp)/('a'*32);folder.mkdir()
            (folder/'job.json').write_text(json.dumps(dict(job_id='a'*32,status='running',pid=os.getpid())))
            with patch.object(jobs.subprocess,'Popen') as launch:
                self.assertEqual(jobs.start('model','a chair')['status'],'busy');launch.assert_not_called()

class AnimationTests(unittest.TestCase):
    def test_forced_motion_reaches_renderer_and_partial_frames_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);(folder/'frames').mkdir();(folder/'frames/frame_0001.png').write_bytes(b'PNG')
            with patch.object(animate,'plan',return_value={'template':'turntable','objects':[]}),patch.object(animate,'render',return_value=subprocess.CompletedProcess([],0,'','')) as render,patch.object(animate,'encode') as encode:
                result=animate.build('test',model='local',out_dir=folder,frames=4,template='bounce')
            self.assertEqual(render.call_args.args[0]['template'],'bounce')
            self.assertIsNone(result['video']);self.assertIn('error',result);encode.assert_not_called()

class ResearchTests(unittest.TestCase):
    def test_voice_topics_are_clean_and_nonresearch_is_untouched(self):
        self.assertEqual(research.intent('Tell me about cache coherence from my textbook'),{'query':'cache coherence','source':'textbooks'})
        self.assertEqual(research.intent('Explain Mercury using Wikipedia'),{'query':'Mercury','source':'wikipedia'})
        self.assertIsNone(research.intent('What is my battery health?'))
        with patch.object(research,'search') as fetch:
            self.assertEqual(research.augment('open Blender'),'open Blender');fetch.assert_not_called()

    def test_unavailable_and_ambiguous_evidence_is_explicit(self):
        with patch.object(research,'search',return_value={'status':'ambiguous','choices':['Mercury planet','Mercury element']}):
            self.assertIn('ask which meaning',research.augment('Tell me about Mercury'))
        with patch.object(research,'search',side_effect=RuntimeError('vault unmounted')):
            self.assertIn('unavailable',research.augment('Tell me about Mercury'))

    def test_source_read_cannot_retrieve_unrelated_or_student_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'test.sqlite'
            with sqlite3.connect(p) as db:
                db.execute('CREATE TABLE sources(id,title,kind,location,page,text)')
                db.execute("INSERT INTO sources VALUES('private','Student submission','case','/private',1,'Private data')")
                db.execute("INSERT INTO sources VALUES('safe','Textbook','book','/book.pdf',42,'Source passage')")
            with patch.object(research,'INDEX',p),patch.object(research,'_index'):
                with self.assertRaises(ValueError):research.read('book:private')
                safe=research.read('book:safe');self.assertEqual(safe['page'],42)
                with self.assertRaises(ValueError):research.read('/etc/passwd')

class ProtocolTests(unittest.TestCase):
    def test_real_stdio_mcp_and_errors(self):
        messages=[{'jsonrpc':'2.0','id':1,'method':'initialize'}, {'jsonrpc':'2.0','method':'notifications/initialized'}, {'jsonrpc':'2.0','id':2,'method':'tools/list'}, {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'pc_build','arguments':{'kind':'shell','subject':'no'}}}]
        done=subprocess.run([sys.executable,'-B','-m','pcstudio.mcp'],input=''.join(json.dumps(m)+'\n' for m in messages),capture_output=True,text=True,env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[2])},check=True)
        rows=[json.loads(line) for line in done.stdout.splitlines()]
        self.assertEqual(len(rows),3)
        self.assertEqual({t['name'] for t in rows[1]['result']['tools']},
                         {'pc_capabilities','pc_research','pc_read_source','pc_build',
                          'pc_job','pc_sim','pc_netmc','pc_graph'})
        self.assertTrue(rows[2]['result']['isError']);self.assertNotIn('Traceback',done.stdout)


class StructuredBuildTests(unittest.TestCase):
    def test_ollama_receives_geometry_schema(self):
        from pcstudio import cli
        from pcstudio.mesh import scene_schema
        response=io.StringIO(json.dumps({'message':{'content':'{"objects":[]}'}}))
        with patch.object(cli.request,'urlopen',return_value=response) as call:
            cli.ask_ollama('a table',model='local-test',json_output=scene_schema())
        payload=json.loads(call.call_args.args[0].data)
        item=payload['format']['properties']['objects']['items']
        self.assertEqual(item['properties']['position']['minItems'],3)
        self.assertEqual(item['properties']['position']['maxItems'],3)
        self.assertGreater(payload['options']['num_predict'],900)

    def test_vault_palette_applies_to_scene_not_only_the_prompt(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(animate,'plan',return_value={'template':'turntable','objects':[{'name':'body'}]}),patch.object(animate,'render',return_value=subprocess.CompletedProcess([],1,'','failed')) as render:
                animate.build('rocket',model='local-test',out_dir=Path(temp),palette={'bg':'#0d0221','text':'#d1f7ff','accent':'#05d9e8'})
            spec=render.call_args.args[0]
            self.assertEqual(spec['background'],[13/255,2/255,33/255])
            self.assertEqual(spec['objects'][0]['color'],[209/255,247/255,1])

    def test_finished_worker_race_uses_published_result(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(jobs,'JOBS',Path(temp)):
            folder=Path(temp)/('a'*32);folder.mkdir();out=folder/'result.obj';out.write_text('mesh')
            file=folder/'job.json';file.write_text(json.dumps(dict(status='running',pid=123)))
            def finished(pid):
                file.write_text(json.dumps(dict(status='complete',artifacts=[str(out)])))
                return False
            with patch.object(jobs,'_alive',side_effect=finished):
                self.assertEqual(jobs.status('a'*32)['status'],'complete')

    def test_terminal_composition_keeps_actual_assets_and_rejects_substitution(self):
        import importlib.util
        if importlib.util.find_spec('termstage') is None:
            self.skipTest('Optional external Termstage project is not installed')
        from pcstudio.terminal_build import library_scene,UnsupportedSubject
        plan={'supported':True,'background':[{'asset':'moon','x':.7,'y':.1,'motion':'still'}],'subject':{'asset':'ship-side','x':.1,'y':.7,'motion':'right'}}
        with patch('pcstudio.cli.ask_ollama',return_value=json.dumps(plan)):
            scene=library_scene('ship moon','local-test',{'style':'mono'})
        self.assertEqual([l['asset'] for l in scene['layers']],['moon','ship-side'])
        self.assertTrue(scene['layers'][1]['motion'])
        with patch('pcstudio.cli.ask_ollama',return_value='{"supported":false,"layers":[]}'):
            with self.assertRaises(UnsupportedSubject):library_scene('something unknown','local-test',{'style':'mono'})

if __name__=='__main__':unittest.main()
