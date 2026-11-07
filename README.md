# Voice Local Resident

[Português brasileiro](README.pt-BR.md) · Local Windows text-to-speech reader for Brazilian Portuguese using Kokoro, F5-TTS and online Edge TTS. Select text and use the configurable reading shortcut (**Ctrl+Alt+S** by default). Settings for each engine are saved separately in the local configuration page.

## Requirements

Windows 10/11, NVIDIA GPU and compatible CUDA driver, Python 3.11, [uv](https://docs.astral.sh/uv/getting-started/installation/), [Git](https://git-scm.com/downloads), [FFmpeg](https://ffmpeg.org/download.html) on PATH, and [AutoHotkey v2](https://www.autohotkey.com/). The setup downloads several gigabytes. This project requires CUDA and was tested on an RTX 3060 Ti with 8 GB; CPU mode is not implemented.

## Install step by step

Open PowerShell and run each block in order. If a command fails, correct the error before continuing.

**1. Download the project:**

```powershell
git clone https://github.com/saitodisse/voz-local.git
cd voz-local
```

**2. Choose the local data directory:**

```powershell
$env:VOZLOCAL_HOME = Join-Path (Split-Path (Get-Location).Path -Parent) 'voz-local-data'
New-Item -ItemType Directory -Force -Path $env:VOZLOCAL_HOME | Out-Null
```

The service uses this folder by default. To use another folder, set `VOZLOCAL_HOME` in every PowerShell session used to start the server. Never commit its contents.

Existing installations previously used `~/Apps/VozLocal` by default. To keep using that folder, set `VOZLOCAL_HOME` to its full path before starting both scripts and the server. If moving data to the new folder, recreate virtual environments there instead of moving them.

**3. Install the main environment:**

```powershell
uv venv --python 3.11 "$env:VOZLOCAL_HOME\.venv"
uv pip install --python "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
uv pip install --python "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -r requirements.txt
& "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

CUDA must print `True`. Otherwise update/check the NVIDIA driver and PyTorch installation. The first Kokoro generation downloads its model and voice.

**4. Install F5 in a separate environment:**

```powershell
uv venv --python 3.11 "$env:VOZLOCAL_HOME\.f5"
uv pip install --python "$env:VOZLOCAL_HOME\.f5\Scripts\python.exe" f5-tts pyarrow==19.0.1 --torch-backend=cu124
```

**5. Download the F5 checkpoint, vocabulary and reference:**

```powershell
New-Item -ItemType Directory -Force -Path "$env:VOZLOCAL_HOME\modelos\f5-pt-br", "$env:VOZLOCAL_HOME\referencias" | Out-Null
& "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -c "import os; from pathlib import Path; from huggingface_hub import hf_hub_download; p=Path(os.environ['VOZLOCAL_HOME'])/'modelos'/'f5-pt-br'; hf_hub_download('firstpixel/F5-TTS-pt-br','pt-br/model_last.safetensors',local_dir=p); hf_hub_download('SWivid/F5-TTS','F5TTS_Base/vocab.txt',local_dir=p)"
Invoke-WebRequest 'https://raw.githubusercontent.com/OHF-Voice/voice-datasets/master/pt_BR/cadu/0000000001.mp3' -OutFile "$env:VOZLOCAL_HOME\referencias\cadu.mp3"
```

The F5 Vocos vocoder downloads on first use. The Cadu reference is CC0; its hard-coded transcript was generated automatically and may need correction. The page currently cannot change the reference or transcript.

## Start and use

For the installed project, run `start.ps1` and `stop.ps1` from PowerShell to start and stop the reader. The start script opens the configuration page and checks whether the port or another reader shortcut is already in use. The stop script targets only this project's processes. On the original user's computer, desktop shortcuts named **Iniciar Voz Local** and **Parar Voz Local** were created; other users can create equivalent shortcuts to these scripts.


From the project folder, open a PowerShell window and run:

```powershell
$env:VOZLOCAL_HOME = Join-Path (Split-Path (Get-Location).Path -Parent) 'voz-local-data'
& "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -X utf8 server.py
```

Leave the window open. Open http://127.0.0.1:8888/, select an engine, adjust its settings and save. In File Explorer, double-click `read_selection.ahk` to start the shortcut listener. Select text and press Ctrl+Alt+S, or configure another combination on the page. Choose **Gravar combinação**, press Ctrl, Alt, Shift or Win together with a key, then save. The listener applies it automatically. It pauses the current shortcut during capture and resumes it when capture ends; an automatic timeout restores it if the page closes unexpectedly. Choose **Desativar** to turn the shortcut off. To stop, exit the AutoHotkey tray icon and press Ctrl+C in the server window. Closing the browser does not stop the server. If port 8888 or the shortcut is already used by an older reader, stop that reader first.

## Edge TTS online

Select **Edge TTS** on the configuration page, choose Francisca, Antonio or Thalita Multilingual, adjust rate, volume and pitch, and save. The configured reading shortcut uses the selected engine. Edge TTS sends selected text over the internet to Microsoft; it does not use the GPU for synthesis. The community-maintained [edge-tts](https://github.com/rany2/edge-tts) library currently requires no API key, but service availability, voices and terms can change. Latency depends on the network and service. FFmpeg converts the response for playback.

For an existing installation, update the main environment with `uv pip install --python "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -r requirements.txt` and restart the reader.

## Tests and limitations

To test Edge settings and real online synthesis in an isolated temporary configuration, run `& "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -X utf8 test_edge.py`; it requires internet and FFmpeg. With this project's server running, run `& "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -X utf8 test_integration.py`. It changes configuration temporarily and restores it; avoid concurrent use. The test requires both models and a GPU and does not test playback or the hotkey. F5 is limited to 500 characters and loads its model for each request. Kokoro loads on first request and is unloaded when F5 is used. The local server has no authentication; keep it bound to localhost.

## Licenses

Application code: MIT. Kokoro weights: Apache 2.0. The [firstpixel F5 pt-BR checkpoint](https://huggingface.co/firstpixel/F5-TTS-pt-br) is CC BY-NC 4.0 and restricts commercial use. [Cadu reference dataset](https://github.com/OHF-Voice/voice-datasets): CC0. Dependencies, models and recordings have separate terms; source code licensing does not override those terms.
