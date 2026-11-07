import io, os, json, re, time, threading, subprocess, asyncio
from pathlib import Path
from typing import Literal
BASE=Path(os.environ.get('VOZLOCAL_HOME', str(Path(__file__).resolve().parent.parent / 'voz-local-data')))
os.environ['HF_HOME']=str(BASE/'cache')
import numpy as np, soundfile as sf, torch, uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, HTMLResponse
from pydantic import BaseModel, Field, field_validator
from kokoro import KPipeline
from phonemizer.backend.espeak.wrapper import EspeakWrapper
import espeakng_loader
EspeakWrapper.set_library(espeakng_loader.get_library_path())
os.environ['ESPEAK_DATA_PATH']=str(espeakng_loader.get_data_path())
CONFIG=BASE/'leitor-config.json'
SHORTCUT_PATTERN=re.compile(r'(?P<modifiers>[!^+#]*)(?P<key>[A-Za-z0-9]|F(?:[1-9]|1[0-9]|2[0-4])|Numpad(?:[0-9]|Add|Sub|Mult|Div|Dot|Enter)|Space|Tab|Enter|Esc|Backspace|Delete|Insert|Home|End|PgUp|PgDn|Up|Down|Left|Right)',re.IGNORECASE)
lock=threading.RLock(); shortcut_capture_lock=threading.Lock(); pipeline=None; shortcut_capture_until=0
class Kokoro(BaseModel):
 voice: Literal['pf_dora','pm_alex','pm_santa']='pf_dora'
 speed: float=Field(default=1,ge=0.7,le=1.3)
class F5(BaseModel):
 speed: float=Field(default=1,ge=0.7,le=1.3)
 nfe_step: int=Field(default=32,ge=8,le=64)
 cfg_strength: float=Field(default=2,ge=0,le=5)
 sway_sampling_coef: float=Field(default=-1,ge=-2,le=1)
 cross_fade_duration: float=Field(default=0.15,ge=0,le=1)
 target_rms: float=Field(default=0.1,ge=0.01,le=0.5)
 seed: int=Field(default=-1,ge=-1,le=2147483647)
 reference: Literal['cadu']='cadu'
class Edge(BaseModel):
 voice: Literal['pt-BR-FranciscaNeural','pt-BR-AntonioNeural','pt-BR-ThalitaMultilingualNeural']='pt-BR-FranciscaNeural'
 rate: int=Field(default=0,ge=-50,le=100)
 volume: int=Field(default=0,ge=-100,le=100)
 pitch: int=Field(default=0,ge=-50,le=50)
class Settings(BaseModel):
 engine: Literal['kokoro','f5','edge']='kokoro'
 shortcut: str=Field(default='^!s',max_length=40)
 kokoro: Kokoro=Kokoro()
 f5: F5=F5()
 edge: Edge=Edge()

 @field_validator('shortcut')
 @classmethod
 def validate_shortcut(cls,value):
  if value=='': return value
  match=SHORTCUT_PATTERN.fullmatch(value)
  if not match: raise ValueError('Use Ctrl, Alt, Shift ou Win com uma tecla compatível, ou desative o atalho.')
  modifiers=match.group('modifiers')
  if not modifiers: raise ValueError('O atalho precisa incluir pelo menos um modificador.')
  if len(set(modifiers))!=len(modifiers): raise ValueError('Não repita modificadores no atalho.')
  return value
class ShortcutCapture(BaseModel):
 enabled: bool
class TTSRequest(BaseModel):
 text: str=Field(min_length=1,max_length=5000)
 voice: str|None=None
 speed: float|None=None

def read_config():
 return Settings.model_validate_json(CONFIG.read_text(encoding='utf-8')) if CONFIG.exists() else Settings()
def save_config(config):
 BASE.mkdir(parents=True,exist_ok=True)
 tmp=CONFIG.with_suffix('.tmp'); tmp.write_text(config.model_dump_json(indent=2),encoding='utf-8'); os.replace(tmp,CONFIG)
def get_pipeline():
 global pipeline
 if pipeline is None:
  pipeline=KPipeline(lang_code='p',repo_id='hexgrad/Kokoro-82M',device='cuda')
 return pipeline
app=FastAPI()
@app.middleware('http')
async def guard(request:Request,call_next):
 origin=request.headers.get('origin')
 if request.url.hostname not in ('127.0.0.1', 'localhost'):
  return Response('Host not allowed',status_code=403)
 if origin and origin != f'{request.url.scheme}://{request.url.netloc}':
  return Response('Origem não permitida',status_code=403)
 return await call_next(request)
@app.get('/',response_class=HTMLResponse)
def home(): return Path(__file__).with_name('configuracao.html').read_text(encoding='utf-8')
@app.get('/health')
def health(): return {'status':'ready','gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}
@app.get('/config')
def config(): return read_config()
@app.get('/shortcut/state')
def shortcut_state():
 global shortcut_capture_until
 settings=read_config()
 with shortcut_capture_lock:
  if shortcut_capture_until<=time.monotonic(): shortcut_capture_until=0
  return {'shortcut':settings.shortcut,'capture':shortcut_capture_until>0}
@app.put('/shortcut/capture')
def set_shortcut_capture(request:ShortcutCapture):
 global shortcut_capture_until
 with shortcut_capture_lock:
  shortcut_capture_until=time.monotonic()+90 if request.enabled else 0
 return {'capture':request.enabled}
@app.put('/config')
def update(settings:Settings):
 with lock: save_config(settings)
 return settings
@app.post('/tts')
def tts(req:TTSRequest):
 global pipeline
 if not req.text.strip(): raise HTTPException(422,'Texto vazio')
 with lock:
  settings=read_config(); t=time.perf_counter()
  if settings.engine=='edge':
   import edge_tts, tempfile
   async def fetch_audio():
    audio=bytearray()
    communicate=edge_tts.Communicate(req.text,settings.edge.voice,rate=f'{settings.edge.rate:+d}%',volume=f'{settings.edge.volume:+d}%',pitch=f'{settings.edge.pitch:+d}Hz')
    async for chunk in communicate.stream():
     if chunk['type']=='audio': audio.extend(chunk['data'])
    return bytes(audio)
   try:
    mp3=asyncio.run(fetch_audio())
    if not mp3: raise RuntimeError('O serviço não retornou áudio.')
    with tempfile.TemporaryDirectory(prefix='voz-edge-') as folder:
     path=Path(folder)/'audio.wav'
     converted=subprocess.run(['ffmpeg','-v','error','-i','pipe:0','-y',str(path)],input=mp3,capture_output=True,timeout=120)
     if converted.returncode: raise RuntimeError('Falha ao converter áudio: '+converted.stderr.decode('utf-8',errors='replace')[-500:])
     result=path.read_bytes()
   except Exception as e: raise HTTPException(502,'Falha no Edge TTS: '+str(e)) from e
  elif settings.engine=='f5':
   if len(req.text)>500: raise HTTPException(422,'F5 aceita até 500 caracteres nesta versão.')
   pipeline=None; torch.cuda.empty_cache()
   import tempfile
   with tempfile.TemporaryDirectory(prefix='voz-f5-') as folder:
    path=Path(folder)/'out.wav'
    cmd=[str(BASE/'.f5/Scripts/python.exe'),'-X','utf8',str(Path(__file__).with_name('f5_worker.py')),req.text,str(path),'cuda',str(BASE/'referencias/cadu.mp3'),'os descontos chegam a setenta e oito por cento e correspondem aos impostos que incidem sobre as mercadorias.',settings.f5.model_dump_json()]
    proc=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=BASE,timeout=300)
    if proc.returncode: raise HTTPException(500,proc.stderr[-1200:])
    result=path.read_bytes()
  else:
   voice=req.voice or settings.kokoro.voice; speed=req.speed if req.speed is not None else settings.kokoro.speed
   if voice not in ('pf_dora','pm_alex','pm_santa') or not 0.7<=speed<=1.3: raise HTTPException(422,'Voz ou velocidade inválida')
   with torch.inference_mode(): chunks=[a.cpu().numpy() for _,_,a in get_pipeline()(req.text,voice=voice,speed=speed) if a is not None]
   if not chunks: raise HTTPException(422,'Sem áudio')
   buffer=io.BytesIO(); sf.write(buffer,np.concatenate(chunks),24000,format='WAV',subtype='PCM_16'); result=buffer.getvalue()
  return Response(result,media_type='audio/wav',headers={'X-Processing-Ms':str(round((time.perf_counter()-t)*1000))})
if __name__=='__main__': uvicorn.run(app,host='127.0.0.1',port=8888,log_level='warning')
