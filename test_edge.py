import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import server

def test_edge():
 with tempfile.TemporaryDirectory() as d:
  server.CONFIG=Path(d)/'settings.json'
  c=TestClient(server.app,base_url="http://127.0.0.1:8888")
  original=c.get('/config').json()
  assert 'edge' in original
  original['engine']='edge'; original['edge']={'voice':'pt-BR-FranciscaNeural','rate':10,'volume':0,'pitch':0}
  r=c.put('/config',json=original); assert r.status_code==200,r.text
  assert c.get('/config').json()['edge']['rate']==10
  r=c.post('/tts',json={'text':'Olá, este é um teste em português brasileiro.'})
  assert r.status_code==200,r.text
  assert r.headers['content-type'].startswith('audio/wav') and r.content[:4]==b'RIFF'
  assert c.put('/config',json={**original,'edge':{'voice':'not-a-voice','rate':0,'volume':0,'pitch':0}}).status_code==422
  print('Edge: persisted settings, validated voice, generated WAV')

if __name__=='__main__': test_edge()
