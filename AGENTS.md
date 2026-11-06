# AGENTS.md

## Project purpose

This repository contains only the Windows resident reader: FastAPI server, browser settings, AutoHotkey shortcut and F5 worker. Do not add the earlier Gradio POCs or copy private machine data into this repository. Keep README.md and README.pt-BR.md consistent when behavior or setup changes.

## Architecture and execution

- `server.py` binds to 127.0.0.1:8888. It validates the host and request origin, serializes generation and configuration writes with a lock, and atomically replaces the local JSON settings file.
- `VOZLOCAL_HOME` selects the private data directory; by default it is `~/Apps/VozLocal`. The Kokoro environment is `.venv`; the isolated F5 environment is `.f5`. Models, user settings, reference recordings and generated audio are excluded from Git.
- Kokoro uses Brazilian Portuguese `lang_code=p`, three official voices and CUDA. Its model loads on demand; F5 generation releases the Kokoro model first.
- Edge TTS uses the community `edge-tts` client and sends selected text to Microsoft; disclose this in the interface and docs. It synthesizes online, then FFmpeg converts the response to WAV. Do not promise unlimited use or fixed latency. Keep its settings independent and backward compatible.
- F5 uses the firstpixel pt-BR checkpoint with `F5TTS_Base`, original vocabulary, Cadu reference and the fixed reference transcript in `server.py`. It runs in a subprocess and reloads on each request. Preserve the 500-character limit unless generation is deliberately redesigned and verified.
- `start.ps1` and `stop.ps1` start and stop this project only; do not terminate unrelated services or silently replace the older reader. Desktop and Windows startup shortcuts are machine-specific.
- `read_selection.ahk` uses Ctrl+Alt+S, preserves the clipboard, posts UTF-8 JSON and plays the returned WAV. Do not create additional global hotkeys without checking collisions and user intent.
- `configuracao.html` is a local app, not a public hosted site. Its controls and validation must stay aligned with Pydantic models and F5 worker arguments. Changes to settings must remain backward compatible or include migration.

## Validation

Run `python -m py_compile server.py f5_worker.py`. `test_edge.py` uses a temporary settings file and performs actual online synthesis; it requires network access and FFmpeg. With the intended service running, use `test_integration.py` for actual synthesis and settings validation; it temporarily changes configuration and restores it. Never run it concurrently with a user session without considering that side effect. The test requires both models and GPU and does not prove physical playback or UI hotkey behavior. Test changes to the browser and AutoHotkey flows separately.

## Privacy, licensing and delivery

Never commit credentials, settings, cache, model weights, recordings, generated audio or personal paths. The application code is MIT; Kokoro weights are Apache 2.0; the firstpixel F5 pt-BR checkpoint is CC BY-NC 4.0. Reference recordings and dependencies have their own licenses. Do not conflate licenses or claim commercial F5 use is permitted. Preserve localhost-only access and the origin check. Do not expose the server publicly.

For changes, update CHANGELOG.md and VERSION when warranted, run relevant tests and `git diff --check`, and keep English documentation and the Brazilian Portuguese translation aligned. Do not publish, tag or push without a user request authorizing it.
