#Requires AutoHotkey v2.0
#SingleInstance Force
#MaxThreadsPerHotkey 1
A_TrayMenu.Add("Configurar vozes", (*) => Run("http://127.0.0.1:8888/"))

JsonEscape(s) {
    s := StrReplace(s, '\', '\\')
    s := StrReplace(s, '"', '\"')
    s := StrReplace(s, '`r', '\r')
    s := StrReplace(s, '`n', '\n')
    s := StrReplace(s, '`t', '\t')
    return s
}

^!s:: {
    saved := ClipboardAll()
    A_Clipboard := ''
    Send '^c'
    if !ClipWait(1.5) {
        A_Clipboard := saved
        TrayTip 'Selecione um texto antes de usar Ctrl+Alt+S.', 'Kokoro'
        return
    }
    text := A_Clipboard
    A_Clipboard := saved
    if !Trim(text)
        return
    try {
        json := '{"text":"' JsonEscape(text) '"}'
        stream := ComObject('ADODB.Stream')
        stream.Type := 2
        stream.Charset := 'utf-8'
        stream.Open()
        stream.WriteText(json)
        stream.Position := 0
        stream.Type := 1
        stream.Position := 3
        body := stream.Read()
        stream.Close()
        req := ComObject('WinHttp.WinHttpRequest.5.1')
        req.SetTimeouts(2000, 2000, 5000, 120000)
        req.Open('POST', 'http://127.0.0.1:8888/tts', false)
        req.SetRequestHeader('Content-Type', 'application/json; charset=utf-8')
        req.Send(body)
        if req.Status != 200
            throw Error('Servidor retornou HTTP ' req.Status)
        path := A_Temp '\kokoro-leitura-' A_TickCount '.wav'
        file := ComObject('ADODB.Stream')
        file.Type := 1
        file.Open()
        file.Write(req.ResponseBody)
        file.SaveToFile(path, 2)
        file.Close()
        SoundPlay path, true
        FileDelete path
    } catch as e {
        TrayTip 'Não foi possível ler o texto: ' e.Message, 'Kokoro'
    }
}
