import contextlib
import io
import unittest
from unittest.mock import patch
from pcstudio import easy

class AskInputTests(unittest.TestCase):
    def test_quoted_question_and_text_option_use_the_same_path_without_audio(self):
        question='Tell me about the Count of Monte Cristo'
        for arguments in ([question],['--text',question]):
            with self.subTest(arguments=arguments),patch.object(easy,'_prepare_question',return_value='local evidence') as prepare,patch.object(easy,'_ask_hermes_chat',return_value=('A sourced answer.',None)) as chat,patch.object(easy,'_record_transcript') as record,patch.object(easy,'_tts_voices') as voices,patch.object(easy,'_confirm') as confirm,contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(easy.main(['ask',*arguments]),0)
                prepare.assert_called_once_with(question,model=easy.ASSISTANT_MODEL)
                chat.assert_called_once_with('local evidence',model=easy.ASSISTANT_MODEL,session_id=None)
                record.assert_not_called();voices.assert_not_called();confirm.assert_not_called()
                self.assertEqual(output.getvalue().strip(),'A sourced answer.')

    def test_positional_question_honors_model_override_on_either_side(self):
        for argv in (['ask','A question','--model','trial-model'],['ask','--model','trial-model','A question']):
            with self.subTest(argv=argv),patch.object(easy,'_prepare_question',return_value='evidence'),patch.object(easy,'_ask_hermes_chat',return_value=('Answer',None)) as chat,contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(easy.main(argv),0)
                self.assertEqual(chat.call_args.kwargs['model'],'trial-model')

    def test_explicit_numeric_question_stays_text(self):
        with patch.object(easy,'_prepare_question',return_value='evidence') as prepare,patch.object(easy,'_ask_hermes_chat',return_value=('Answer',None)),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(easy.main(['ask','--text','1984']),0)
            self.assertEqual(prepare.call_args.args[0],'1984')

    def test_empty_or_conflicting_questions_fail_without_recording(self):
        for argv in (['ask',''],['ask','  '],['ask','--text',''],['ask','one question','--text','another question'],['ask','--text','another question','one question']):
            with self.subTest(argv=argv),patch.object(easy,'_record_transcript') as record,contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as raised:
                easy.main(argv)
            self.assertEqual(raised.exception.code,2);record.assert_not_called()

    def test_voice_duration_and_granger_standby_remain_compatible(self):
        for argv,seconds,standby in [(['ask'],18,False),(['ask','30'],30,False),(['granger','30'],30,True)]:
            with self.subTest(argv=argv),contextlib.ExitStack() as stack:
                for name,value in [('_tts_voices',{}),('_load_voice_default',None),('_load_confirm_default','button'),('_local_tools',{})]:
                    stack.enter_context(patch.object(easy,name,return_value=value))
                converse=stack.enter_context(patch.object(easy,'_converse'))
                wait=stack.enter_context(patch.object(easy,'_standby'))
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                self.assertEqual(easy.main([*argv,'--no-play','--no-voice-id']),0)
                active=wait if standby else converse;inactive=converse if standby else wait
                active.assert_called_once();inactive.assert_not_called()
                self.assertEqual(active.call_args.args[0].seconds,seconds)

    def test_positional_build_uses_existing_job_route(self):
        report={'status':'queued','job_id':'a'*32,'kind':'model','subject':'a table'}
        with patch.object(easy.jobs,'start',return_value=report) as start,patch.object(easy,'_ask_hermes_chat') as chat,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(easy.main(['ask','Build a 3D model of a table']),0)
            start.assert_called_once_with(kind='model',subject='a table');chat.assert_not_called()

if __name__=='__main__':unittest.main()
