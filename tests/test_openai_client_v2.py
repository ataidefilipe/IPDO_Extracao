from core.openai_client_v2 import chamar_gpt_v2

def test_mock_responses_api(monkeypatch):
    class FakeResp:
        output_text = '{"ok": true}'

    class FakeClient:
        def responses(self):
            return self
        def create(self, **kwargs):
            return FakeResp()

    monkeypatch.setattr("core.openai_client_v2.client", FakeClient())

    out = chamar_gpt_v2("teste")
    assert out["ok"] is True
