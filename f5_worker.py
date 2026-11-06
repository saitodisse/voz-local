import sys, os, json
from pathlib import Path
base=Path(os.environ.get('VOZLOCAL_HOME', str(Path.home() / 'Apps' / 'VozLocal')))
os.environ['HF_HOME']=str(base/'cache')
from f5_tts.api import F5TTS
text,out,device,ref,ref_text,settings=sys.argv[1:]
s=json.loads(settings)
model=F5TTS(model='F5TTS_Base',ckpt_file=str(base/'modelos/f5-pt-br/pt-br/model_last.safetensors'),vocab_file=str(base/'modelos/f5-pt-br/F5TTS_Base/vocab.txt'),device=device)
model.infer(ref_file=ref,ref_text=ref_text,gen_text=text.lower(),file_wave=out,speed=s['speed'],nfe_step=s['nfe_step'],cfg_strength=s['cfg_strength'],sway_sampling_coef=s['sway_sampling_coef'],cross_fade_duration=s['cross_fade_duration'],target_rms=s['target_rms'],seed=None if s['seed']==-1 else s['seed'])
