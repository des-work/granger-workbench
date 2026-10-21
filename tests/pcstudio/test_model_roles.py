import io,json,unittest
from types import SimpleNamespace
from unittest.mock import patch
from pcstudio import mcp,easy,cli,jobs

class ModelRoleTests(unittest.TestCase):
    def snapshot(self,installed):
        response=io.BytesIO(json.dumps({'models':[{'name':n} for n in installed]}).encode())
        opener=SimpleNamespace(open=lambda *a,**k:response)
        with patch.object(easy,'ASSISTANT_MODEL','conversation'),patch.object(jobs,'MODEL','builder'),patch.object(cli,'DEFAULT_VISION_MODEL','vision'),patch.object(mcp,'build_opener',return_value=opener),patch.object(mcp.research,'_kb',return_value=SimpleNamespace(books=lambda:[],BASE='local')),patch.object(mcp.research,'catalog',return_value={}),patch.object(mcp,'_hermes_configuration',return_value={'browser':{},'inference':{}}):
            return mcp.capabilities()['local_ai']

    def test_separate_conversation_build_and_vision_models(self):
        result=self.snapshot(['conversation','builder','vision'])
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['conversation_model'],'conversation')
        self.assertEqual(result['build_planning_model'],'builder')
        self.assertEqual(result['vision_model'],'vision')
        self.assertEqual(result['missing_models'],[])

    def test_missing_conversation_is_reported_even_if_builder_exists(self):
        result=self.snapshot(['builder','vision'])
        self.assertEqual(result['status'],'model_missing')
        self.assertEqual(result['missing_models'],['conversation'])

if __name__=='__main__':unittest.main()
