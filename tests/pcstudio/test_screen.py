import argparse
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from pcstudio import screen,cli,easy

OBS={'summary':'I see a terminal showing a missing-file error.','visible_text':'File not found: notes.txt','uncertainties':''}

class IntentTests(unittest.TestCase):
    def test_initial_look_and_refresh_phrases(self):
        for q in ['take a look at this','Take a look at this.','have a look','look at my screen','can you see this?','take another look','look again','grab a screenshot']:
            with self.subTest(q=q):self.assertEqual(screen.intent(q),'look')

    def test_closer_spatial_and_semantic_sections(self):
        for q in ['take a closer look','look at the top right','focus on the error panel','read the question','zoom in on the paragraph']:
            with self.subTest(q=q):self.assertEqual(screen.intent(q,True),'focus')

    def test_followups_need_context_unless_screen_explicit(self):
        for q in ['What does this mean?','help me answer this question','What is the answer?','What should I write?','How do I fix it?']:
            with self.subTest(q=q):
                self.assertEqual(screen.intent(q,True),'question');self.assertIsNone(screen.intent(q,False))
        self.assertEqual(screen.intent('Explain the question on my screen'),'question')

    def test_unrelated_requests_and_actions_keep_existing_routes(self):
        for q in ['Tell me about Mercury','Explain cache coherence from my textbook','Which local AI model are you using?','Open Blender','Build a 3D model of a table','What is my CPU temperature?','Is the build status complete?']:
            with self.subTest(q=q):self.assertIsNone(screen.intent(q,True))

    def test_screen_context_can_be_cleared(self):
        self.assertEqual(screen.intent('forget the screen',True),'clear')

    def test_deterministic_spatial_regions_and_invalid_bounds(self):
        self.assertEqual(screen.spatial_bounds('look at the top-right'),(.5,0,1,.5))
        self.assertEqual(screen.spatial_bounds('lower left section'),(0,.5,.5,1))
        self.assertEqual(screen.spatial_bounds('middle'),(.2,.2,.8,.8))
        for bad in [[0,0,2,1],[.6,0,.4,1],[0,0,0,1],[0,0,float('nan'),1],[False,0,1,1],None]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):screen.checked_bounds(bad)

class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.frame=self.root/'original.png'
        Image.new('RGB',(2000,1000),'white').save(self.frame)
        self.session=screen.ScreenSession(self.root)
        self.capture=patch.object(cli,'capture_screen',return_value=self.frame).start()
        self.vision=patch.object(cli,'ask_ollama',return_value=json.dumps(OBS)).start()
        self.ocr=patch.object(screen,'local_ocr',return_value='File not found: notes.txt').start()
        self.addCleanup(patch.stopall)

    def test_first_look_is_one_sentence_from_real_observation(self):
        turn=self.session.prepare('take a look at this')
        self.assertEqual(turn.answer,OBS['summary']);self.assertIsNone(turn.prompt)
        self.assertEqual(self.session.frame,self.frame)
        self.assertTrue(self.vision.call_args.kwargs['image'].is_file())
        self.assertIn('untrusted',self.vision.call_args.args[0])
        self.assertEqual(self.vision.call_args.kwargs['model'],cli.DEFAULT_VISION_MODEL)

    def test_confirmation_question_still_gets_short_identification(self):
        turn=self.session.prepare('Can you see this?')
        self.assertEqual(turn.answer,OBS['summary']);self.assertIsNone(turn.prompt)

    def test_followup_uses_retained_frame_and_visible_text(self):
        self.session.prepare('take a look at this')
        turn=self.session.prepare('What does this mean?')
        self.capture.assert_called_once()
        self.assertIsNone(turn.answer);self.assertIn('File not found: notes.txt',turn.prompt)
        self.assertIn('untrusted reference data',turn.prompt);self.assertIn('captured_at',turn.prompt)
        self.assertIn('not a live feed',turn.prompt)

    def test_closer_look_refreshes_and_crops_requested_quadrant(self):
        self.session.prepare('take a look at this')
        turn=self.session.prepare('look at the top right')
        self.assertEqual(self.capture.call_count,2)
        with Image.open(self.session.view) as image:self.assertEqual(image.size,(1000,500))
        with Image.open(self.frame) as image:self.assertEqual(image.size,(2000,1000))
        self.assertEqual(turn.answer,OBS['summary'])

    def test_generic_closer_look_keeps_higher_resolution_original(self):
        self.session.prepare('take a look at this')
        self.session.prepare('take a closer look')
        with Image.open(self.session.view) as image:self.assertEqual(image.size,(2000,1000))

    def test_named_section_is_located_then_cropped(self):
        self.session.prepare('take a look at this')
        self.vision.side_effect=[json.dumps({'found':True,'label':'error panel','bounds':[.1,.2,.7,.8]}),json.dumps(OBS)]
        turn=self.session.prepare('focus on the error panel')
        self.assertEqual(self.session.focus,'error panel')
        with Image.open(self.session.view) as image:
            self.assertGreater(image.width,1200);self.assertGreater(image.height,600)
        self.assertEqual(turn.answer,OBS['summary'])

    def test_missing_named_section_does_not_invent_a_success(self):
        self.vision.return_value=json.dumps({'found':False,'label':'','bounds':[0,0,1,1]})
        turn=self.session.prepare('focus on the fourth question')
        self.assertIn("couldn't identify",turn.answer);self.assertIsNone(turn.prompt)

    def test_unavailable_capture_does_not_claim_to_see_anything(self):
        self.capture.side_effect=RuntimeError('capture unavailable')
        turn=self.session.prepare('take a look at this')
        self.assertIn("couldn't read",turn.answer);self.assertIsNone(self.session.frame)
        self.vision.assert_not_called()

    def test_model_failure_does_not_confirm_screen(self):
        self.vision.return_value='not JSON'
        turn=self.session.prepare('take a look at this')
        self.assertIn("couldn't read",turn.answer)

    def test_clear_forgets_visual_context(self):
        self.session.prepare('take a look at this')
        self.session.prepare('forget the screen')
        self.assertIsNone(self.session.frame)
        self.assertIsNone(self.session.prepare('What does this mean?'))
        self.assertEqual(self.session.history,[])

    def test_initial_question_can_capture_read_and_pass_evidence_to_reasoner(self):
        turn=self.session.prepare('Help me answer the question on my screen')
        self.capture.assert_called_once();self.assertIn('File not found: notes.txt',turn.prompt)
        self.assertIsNone(turn.answer)

class OCRTests(unittest.TestCase):
    def test_existing_ocr_output_is_used_as_an_untrusted_reading_aid(self):
        result=subprocess.CompletedProcess([],0,'Question: 7 x 6?\nB. 42\n','')
        with patch.object(screen.shutil,'which',return_value='/usr/bin/tesseract'),patch.object(screen.subprocess,'run',return_value=result):
            self.assertIn('B. 42',screen.local_ocr(Path('/tmp/synthetic.png')))

    def test_missing_or_failed_ocr_falls_back_to_vision(self):
        with patch.object(screen.shutil,'which',return_value=None),patch.object(screen.subprocess,'run') as run:
            self.assertEqual(screen.local_ocr(Path('/tmp/synthetic.png')),'');run.assert_not_called()
        with patch.object(screen.shutil,'which',return_value='/usr/bin/tesseract'),patch.object(screen.subprocess,'run',side_effect=subprocess.TimeoutExpired('ocr',15)):
            self.assertEqual(screen.local_ocr(Path('/tmp/synthetic.png')),'')

class CaptureTests(unittest.TestCase):
    def test_capture_uses_fresh_private_folder_and_returns_actual_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            old=Path(tmp)/'old.png';old.write_bytes(b'old')
            def run(command,**kwargs):
                self.assertTrue(kwargs['check']);self.assertEqual(kwargs['timeout'],30)
                p=Path(command[command.index('--save-dir')+1])/'capture.png'
                Image.new('RGB',(50,30),'white').save(p)
            with patch.object(cli.subprocess,'run',side_effect=run):actual=cli.capture_screen(Path(tmp))
            self.assertNotEqual(actual,old);self.assertTrue(actual.is_file())
            self.assertEqual(actual.stat().st_mode & 0o777,0o600)
            self.assertEqual(actual.parent.stat().st_mode & 0o777,0o700)

    def test_no_image_or_timeout_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(cli.subprocess,'run'),self.assertRaisesRegex(RuntimeError,'did not save'):cli.capture_screen(Path(tmp))
            with patch.object(cli.subprocess,'run',side_effect=subprocess.TimeoutExpired('capture',30)),self.assertRaisesRegex(RuntimeError,'capture failed'):cli.capture_screen(Path(tmp))

class ConversationTests(unittest.TestCase):
    def test_granger_identifies_then_retains_screen_for_help_without_action_confirmation(self):
        args=argparse.Namespace(seconds=18,no_play=True,model='orchestrator')
        session=screen.ScreenSession(Path('/tmp/unused-test-screen'))
        replies=[screen.ScreenTurn(answer='I see a math question.'),screen.ScreenTurn(prompt='Help answer this [Local screen evidence: 2 + 2]')]
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(easy.cli,'aec_available',return_value=False))
            stack.enter_context(patch.object(easy.screen,'ScreenSession',return_value=session))
            prepare=stack.enter_context(patch.object(session,'prepare',side_effect=replies))
            stack.enter_context(patch.object(easy,'_record_transcript',side_effect=[('Help me answer this question',None),('goodbye',None)]))
            chat=stack.enter_context(patch.object(easy,'_ask_hermes_chat',return_value=('Four.','saved-session')))
            confirm=stack.enter_context(patch.object(easy,'_confirm'))
            stack.enter_context(patch.object(easy,'_prepare_question',side_effect=AssertionError('Screen question must bypass tmux/research')))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            easy._converse(args,None,'voice',{},None,first_turn=('take a look at this',None))
            self.assertEqual(prepare.call_count,2);chat.assert_called_once()
            self.assertIn('Local screen evidence',chat.call_args.args[0]);confirm.assert_not_called()

    def test_typed_look_uses_same_screen_path_without_general_chat(self):
        with patch.object(easy.screen.ScreenSession,'prepare',return_value=screen.ScreenTurn(answer='I see a document.')) as prepare,patch.object(easy,'_ask_hermes_chat') as chat,contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(easy.main(['ask','take a look at this']),0)
        prepare.assert_called_once_with('take a look at this');chat.assert_not_called()
        self.assertEqual(out.getvalue().strip(),'I see a document.')

if __name__=='__main__':unittest.main()
