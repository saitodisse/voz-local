# Voice Local Resident

[Read in English](README.md) · Leitor local de texto em português brasileiro para Windows com Kokoro, F5-TTS e Edge TTS on-line. Selecione um texto e pressione **Ctrl + Alt + S**. A página local salva configurações separadas para cada motor.

## Antes de começar

Você precisa de Windows 10/11, GPU NVIDIA com driver compatível com CUDA, Python 3.11, [uv](https://docs.astral.sh/uv/getting-started/installation/), [Git](https://git-scm.com/downloads), [FFmpeg](https://ffmpeg.org/download.html) no PATH e [AutoHotkey v2](https://www.autohotkey.com/). A instalação baixa vários gigabytes e precisa de internet. O projeto foi testado em uma RTX 3060 Ti de 8 GB; a versão atual exige CUDA e não oferece modo CPU.

O checkpoint brasileiro do F5 tem licença **CC BY-NC 4.0, restrita a uso não comercial**. As licenças do código, dos modelos e das gravações são independentes.

## Instalação passo a passo

Abra o PowerShell e execute cada bloco na ordem. Se algum comando falhar, resolva o erro antes de continuar.

**1. Baixe o projeto:**

```powershell
git clone https://github.com/saitodisse/voz-local.git
cd voz-local
```

**2. Escolha a pasta para modelos e ambientes:**

```powershell
$env:VOZLOCAL_HOME = Join-Path $env:USERPROFILE 'Apps\VozLocal'
New-Item -ItemType Directory -Force -Path $env:VOZLOCAL_HOME | Out-Null
```

Essa é também a pasta padrão do servidor. Se escolher outra, defina a variável novamente em cada janela do PowerShell usada para iniciar o programa. Não envie o conteúdo dessa pasta ao GitHub.

**3. Instale o ambiente principal e confirme a GPU:**

```powershell
uv venv --python 3.11 "$env:VOZLOCAL_HOME\.venv"
uv pip install --python "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
uv pip install --python "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -r requirements.txt
& "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

O resultado deve mostrar `CUDA: True`. Se mostrar `False`, confira o driver NVIDIA e a instalação do PyTorch. O modelo Kokoro e a voz escolhida serão baixados na primeira geração.

**4. Instale o F5 em um ambiente separado:**

```powershell
uv venv --python 3.11 "$env:VOZLOCAL_HOME\.f5"
uv pip install --python "$env:VOZLOCAL_HOME\.f5\Scripts\python.exe" f5-tts pyarrow==19.0.1 --torch-backend=cu124
```

**5. Baixe o modelo F5, seu vocabulário e a referência Cadu:**

```powershell
New-Item -ItemType Directory -Force -Path "$env:VOZLOCAL_HOME\modelos\f5-pt-br", "$env:VOZLOCAL_HOME\referencias" | Out-Null
& "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -c "import os; from pathlib import Path; from huggingface_hub import hf_hub_download; p=Path(os.environ['VOZLOCAL_HOME'])/'modelos'/'f5-pt-br'; hf_hub_download('firstpixel/F5-TTS-pt-br','pt-br/model_last.safetensors',local_dir=p); hf_hub_download('SWivid/F5-TTS','F5TTS_Base/vocab.txt',local_dir=p)"
Invoke-WebRequest 'https://raw.githubusercontent.com/OHF-Voice/voice-datasets/master/pt_BR/cadu/0000000001.mp3' -OutFile "$env:VOZLOCAL_HOME\referencias\cadu.mp3"
```

O vocoder Vocos será baixado no primeiro uso do F5. A referência Cadu é CC0; a transcrição utilizada pelo programa foi gerada automaticamente e pode precisar de correção. A página ainda não permite trocar a referência nem editar essa transcrição.

## Como iniciar e usar

Para iniciar e parar pelo projeto, execute `start.ps1` e `stop.ps1` no PowerShell. O início abre a página de configuração e verifica se a porta ou outro atalho de leitura já estão ocupados. A parada procura apenas processos deste projeto. No computador original, foram criados os atalhos **Iniciar Voz Local** e **Parar Voz Local** na área de trabalho; em outra máquina, você pode criar atalhos equivalentes para esses arquivos.


Na pasta do projeto, abra uma janela do PowerShell e execute:

```powershell
$env:VOZLOCAL_HOME = Join-Path $env:USERPROFILE 'Apps\VozLocal'
& "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -X utf8 server.py
```

Se escolheu outra pasta para os modelos, coloque o caminho escolhido na variável. Mantenha essa janela aberta. Acesse http://127.0.0.1:8888/, escolha o motor, ajuste seus parâmetros e clique em **Salvar configurações**. No Explorador de Arquivos, dê dois cliques em `read_selection.ahk` para iniciar o atalho. Selecione um texto e pressione **Ctrl + Alt + S**.

Para parar, saia pelo ícone do AutoHotkey na bandeja e pressione Ctrl+C na janela do servidor. Fechar o navegador não encerra o servidor. Se a porta 8888 ou o atalho já estiverem em uso pelo leitor anterior, encerre-o antes de iniciar esta versão.

## Edge TTS pela internet

Na página de configuração, escolha **Edge TTS**, selecione Francisca, Antonio ou Thalita Multilingual, ajuste velocidade, volume e tonalidade e salve. O mesmo atalho Ctrl + Alt + S usa o motor selecionado. O Edge TTS envia o texto selecionado pela internet para a Microsoft e não usa a GPU para sintetizar a voz. A biblioteca comunitária [edge-tts](https://github.com/rany2/edge-tts) atualmente não exige chave de API, mas a disponibilidade, as vozes e as condições do serviço podem mudar. A demora depende da rede e do serviço. O FFmpeg converte o áudio para reprodução.

Para atualizar uma instalação existente, execute `uv pip install --python "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -r requirements.txt` e reinicie o leitor.

## Testes e limites

Para testar as configurações do Edge e gerar áudio real usando uma configuração temporária isolada, execute `& "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -X utf8 test_edge.py`; são necessários internet e FFmpeg. Com o servidor deste projeto rodando, execute `& "$env:VOZLOCAL_HOME\.venv\Scripts\python.exe" -X utf8 test_integration.py`. O teste muda as configurações temporariamente e as restaura; não use o leitor ao mesmo tempo. Ele exige os dois modelos e a GPU e não testa a reprodução física nem o atalho. Para testar em outra porta, defina `VOZLOCAL_TEST_URL` com a URL local correspondente.

O F5 aceita até 500 caracteres e carrega seu modelo em cada requisição. O Kokoro carrega na primeira utilização e é descarregado ao usar o F5. O servidor não tem autenticação; mantenha-o acessível somente em localhost. As configurações ficam em `leitor-config.json` dentro da pasta de dados local.

## Licenças

Código deste projeto: MIT. Pesos do Kokoro: Apache 2.0. O [checkpoint F5-TTS pt-BR](https://huggingface.co/firstpixel/F5-TTS-pt-br) é CC BY-NC 4.0, com restrição comercial. O [acervo da referência Cadu](https://github.com/OHF-Voice/voice-datasets) informa CC0. Confira as condições de cada dependência, modelo e gravação; a licença do código não altera as licenças dos modelos.
