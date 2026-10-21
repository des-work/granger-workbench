"""Both spoken entry points receive actual local design metadata before Hermes."""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from pcstudio import easy

BRIDGE=Path(os.environ.get('ULTRA_DESIGN_TEST_BRIDGE',str(easy.DESIGN_ASSETS_SCRIPT)))

class VoiceDesignTests(unittest.TestCase):
    def test_real_prefetch_contains_selected_profile_layout_art_and_policy(self):
        with patch.object(easy,'DESIGN_ASSETS_SCRIPT',BRIDGE):
            result=easy._augment_design_question('Which assets suit a high fashion website?')
        self.assertIn('atelier-spread',result);self.assertIn('couture-silhouette',result)
        self.assertIn('high-fashion',result);self.assertIn('Preserve',result)
        self.assertNotIn('@keyframes',result);self.assertLess(len(result),6000)

    def test_spoken_named_theme_is_detected_from_the_live_index(self):
        with patch.object(easy,'DESIGN_ASSETS_SCRIPT',BRIDGE):
            self.assertIn('reading-room',easy._augment_design_question('Try dark academia'))
            self.assertIn('nordic-catalog',easy._augment_design_question('Use Nordic'))
            self.assertFalse(easy._is_design_request('Tell me about Nordic history'))

    def test_ordinary_question_does_not_read_the_vault(self):
        with patch.object(easy,'_design_snapshot') as fetch:
            question='What is the capital of Norway?'
            self.assertEqual(easy._augment_design_question(question),question)
            fetch.assert_not_called()

    def test_unavailable_vault_never_silently_uses_an_outside_theme(self):
        with patch.object(easy,'_design_snapshot',return_value=None):
            result=easy._augment_design_question('Make a website')
        self.assertIn('unavailable',result);self.assertIn('ask before',result)
        self.assertIn('Do not invent vault asset IDs',result)

    def test_failed_bridge_is_handled_without_claiming_assets_were_loaded(self):
        with patch.object(easy,'DESIGN_ASSETS_SCRIPT',BRIDGE),patch.object(easy.subprocess,'run',side_effect=subprocess.TimeoutExpired('bridge',12)):
            self.assertIsNone(easy._design_snapshot('a website'))

    def _entry(self,command,question):
        asked=[]
        def answer(text,**kwargs):asked.append(text);return 'A local test answer.','test-session'
        def standby(args,voice,mode,tools,voiceid):
            return easy._converse(args,voice,mode,tools,voiceid,first_turn=(question,None))
        heard=[('goodbye',None)] if command=='granger' else [(question,None),('goodbye',None)]
        with contextlib.ExitStack() as stack:
            for target,value in [('_tts_voices',{}),('_load_voice_default',Path('/tmp/test-voice.onnx')),('_load_confirm_default','button'),('_local_tools',{})]:
                stack.enter_context(patch.object(easy,target,return_value=value))
            stack.enter_context(patch.object(easy,'DESIGN_ASSETS_SCRIPT',BRIDGE))
            stack.enter_context(patch.object(easy.cli,'aec_available',return_value=False))
            stack.enter_context(patch.object(easy,'_record_transcript',side_effect=heard))
            stack.enter_context(patch.object(easy,'_ask_hermes_chat',side_effect=answer))
            confirm=stack.enter_context(patch.object(easy,'_confirm'))
            stack.enter_context(patch.object(easy,'_standby',side_effect=standby))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            code=easy.main([command,'--no-play','--no-voice-id'])
        self.assertEqual(code,0);self.assertEqual(len(asked),1);confirm.assert_not_called()
        return asked[0]

    def test_pc_ask_uses_the_vault_before_answering(self):
        self.assertIn('nordic-catalog',self._entry('ask','Which local assets suit a Nordic website?'))

    def test_pc_granger_uses_the_same_vault_path(self):
        self.assertIn('reading-room',self._entry('granger','Which design assets suit a dark academia website?'))

    def test_design_question_keeps_actual_terminal_evidence(self):
        with patch.object(easy.workbench,'terminal_context',return_value='styles.css:44 INVALID SELECTOR'):
            question=self._entry('ask','What is this CSS error in my terminal?')
        self.assertIn('styles.css:44 INVALID SELECTOR',question)
        self.assertIn('Ultra-PC design facts',question)

    def test_normal_health_question_still_receives_real_readings(self):
        with patch.object(easy,'_device_snapshot',return_value={'battery':{'percentage':83.5}}):
            question=self._entry('ask','What is my battery health?')
        self.assertIn('83.5',question)
        self.assertNotIn('Ultra-PC design facts',question)

    def test_voice_prompt_describes_real_export_capability_without_fake_success(self):
        self.assertIn('Ultra-PC vault',easy.SPEAKABLE_PREFIX)
        self.assertIn('only after the tool confirms it',easy.SPEAKABLE_PREFIX)
        self.assertIn('Browser tools can navigate',easy.SPEAKABLE_PREFIX)
        self.assertIn('do not claim to control the existing desktop or user tabs',easy.SPEAKABLE_PREFIX)

if __name__=='__main__':unittest.main()
