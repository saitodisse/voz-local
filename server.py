import io, os, json, time, threading, subprocess
from pathlib import Path
from typing import Literal
BASE=Path(os.environ.get('VOZLOCAL_HOME', str(Path.home() / 'Apps' / 'VozLocal')))
os.environ['HF_HOME']=str(BASE/'cache')
import numpy as np, soundfile as sf, torch, uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, HTMLResponse
from pydantic import BaseModel, Field
from kokoro import KPipeline
from phonemizer.backend.espeak.wrapper import EspeakWrapper
import espeakng_loader
EspeakWrapper.set_library(espeakng_loader.get_library_path())
os.environ['ESPEAK_DATA_PATH']=str(espeakng_loader.get_data_path())
CONFIG=BASE/'leitor-config.json'
lock=threading.RLock(); pipeline=None
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
class Settings(BaseModel):
 engine: Literal['kokoro','f5']='kokoro'
 kokoro: Kokoro=Kokoro()
 f5: F5=F5()
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
  if settings.engine=='f5':
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
