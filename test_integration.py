import os, requests
u=os.environ.get('VOZLOCAL_TEST_URL','http://127.0.0.1:8888'); old=requests.get(u+'/config').json()
try:
 s=old.copy();s['engine']='kokoro';s['kokoro']={'voice':'pm_alex','speed':1.1};r=requests.put(u+'/config',json=s);assert r.status_code==200,r.text
 assert requests.get(u+'/config').json()['kokoro']['voice']=='pm_alex'
 r=requests.post(u+'/tts',json={'text':'Olá, este é um teste de voz brasileira.'},timeout=120);assert r.status_code==200 and r.content[:4]==b'RIFF',r.text[:500];print('Kokoro OK',r.headers.get('X-Processing-Ms'))
 s['engine']='f5';r=requests.put(u+'/config',json=s);assert r.status_code==200,r.text
 r=requests.post(u+'/tts',json={'text':'Olá, esta é uma prova de voz brasileira.'},timeout=240);assert r.status_code==200 and r.content[:4]==b'RIFF',r.text[:500];print('F5 OK',r.headers.get('X-Processing-Ms'))
 assert requests.put(u+'/config',json={**s,'engine':'invalid'}).status_code==422
finally:
 requests.put(u+'/config',json=old)
