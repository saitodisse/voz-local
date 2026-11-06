# Voice Local Resident

A private, local Windows text-to-speech reader for Brazilian Portuguese. Select text in any app and press **Ctrl+Alt+S**. Choose Kokoro or F5-TTS and save their independent settings in the local web interface.

## Features

- Local-only HTTP service and configuration page on `127.0.0.1:8888`.
- Kokoro Brazilian voices Dora, Alex and Santa, with selectable speed. The model remains loaded after its first use.
- F5-TTS Brazilian Portuguese with separate speed, sampling, diffusion steps, guidance, crossfade, RMS and seed settings. The F5 model loads in a separate process for each request.
- Windows tray shortcut restores the clipboard after copying the selection.
- Configuration, models, voice samples and generated audio remain on your computer and are not part of this repository.

## Requirements

Windows 10/11, NVIDIA GPU with a compatible CUDA driver, Python 3.11, `uv`, FFmpeg on PATH, and AutoHotkey v2. This project was tested on an RTX 3060 Ti with 8 GB. GPU use and response time depend on other applications.

## Setup

Install AutoHotkey v2 and FFmpeg, then create two isolated Python 3.11 environments at `.venv` and `.f5` inside the model directory. Install CUDA 12.4 PyTorch in both, install `requirements.txt` in `.venv`, and install `f5-tts` plus `pyarrow==19.0.1` in `.f5`. Download the model assets described below; they occupy several gigabytes. The setup uses the CC0 Cadu voice sample from the Open Home Foundation; the included transcript is machine-generated and may need correction. Existing installations can set `VOZLOCAL_HOME` to their existing model directory instead.

Run `& "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" server.py` in PowerShell, then run `read_selection.ahk` with AutoHotkey v2. Set `VOZLOCAL_HOME` to the model directory first. Open <http://127.0.0.1:8888/> to configure it. The interface is in Brazilian Portuguese. Save settings before reading. `Ctrl+Alt+S` copies the selected text, requests audio locally and plays it. F5 accepts at most 500 characters per request. The service reads the configuration on every request; the engines do not share voice or speed settings.

For a machine configured in this project chat, the default model directory is `C:\Users\saito\Apps\VozLocal`. To use another location, set `VOZLOCAL_HOME` before starting the service. Files include `modelos/f5-pt-br/pt-br/model_last.safetensors`, `modelos/f5-pt-br/F5TTS_Base/vocab.txt`, and `referencias/cadu.mp3`. The Kokoro and Vocos models are downloaded on first use. FFmpeg must be available to the F5 environment.

## Tests

With the service running, `python test_integration.py` exercises configuration persistence, validation and actual audio generation with both engines. It temporarily changes settings and restores them afterward; avoid using the service while running it.

## Licenses

The project code is MIT licensed. Kokoro weights are Apache 2.0. The separately downloaded [firstpixel F5-TTS pt-BR checkpoint](https://huggingface.co/firstpixel/F5-TTS-pt-br) is CC BY-NC 4.0: model weights and output have non-commercial restrictions. Individual dependencies and voice references have their own terms. Do not assume an open-source code license overrides model licenses.

## Limitations

The listener starts with the active Windows session; startup registration is optional and machine-specific. It currently uses Cadu as the F5 reference. Audio playback is local. There is no network authentication, so keep the service bound to localhost. The site does not expose all training or model-loading parameters; it exposes the supported inference controls listed in the [F5 API](https://github.com/SWivid/F5-TTS/blob/main/src/f5_tts/api.py) and the Kokoro voice and speed controls relevant to this reader.
