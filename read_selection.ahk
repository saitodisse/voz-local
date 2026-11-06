#Requires AutoHotkey v2.0
#SingleInstance Force
#MaxThreadsPerHotkey 1

A_TrayMenu.Add("Configurar vozes", (*) => Run("http://127.0.0.1:8888/"))

activeShortcut := ""
configuredShortcut := "^!s"
shortcutConfigRead := false
captureModeActive := false
lastRejectedShortcut := ""
RefreshShortcut()
if !shortcutConfigRead
    ApplyShortcut("^!s")
SetTimer RefreshShortcut, 250

JsonEscape(s) {
    s := StrReplace(s, '\', '\\')
    s := StrReplace(s, '"', '\"')
    s := StrReplace(s, '`r', '\r')
    s := StrReplace(s, '`n', '\n')
    s := StrReplace(s, '`t', '\t')
    return s
}

RefreshShortcut() {
    global activeShortcut, shortcutConfigRead, configuredShortcut, captureModeActive, lastRejectedShortcut
    try {
        request := ComObject('WinHttp.WinHttpRequest.5.1')
        request.SetTimeouts(250, 250, 250, 250)
        request.Open('GET', 'http://127.0.0.1:8888/shortcut/state', false)
        request.Send()
        if request.Status != 200
            return
        if !RegExMatch(request.ResponseText, '"shortcut"\s*:\s*"([^"]*)"', &match)
            return
        nextShortcut := match[1]
        if !RegExMatch(request.ResponseText, '"capture"\s*:\s*(true|false)', &captureMatch)
            return
        shortcutConfigRead := true
        if (nextShortcut != configuredShortcut)
            lastRejectedShortcut := ''
        configuredShortcut := nextShortcut
        captureModeActive := captureMatch[1] = 'true'
        if captureModeActive
            ApplyShortcut('', false)
        else if (configuredShortcut != activeShortcut && configuredShortcut != lastRejectedShortcut)
            ApplyShortcut(configuredShortcut)
    } catch {
        ; Keep the last working hotkey if the local server is restarting.
    }
}

ApplyShortcut(nextShortcut, notify := true) {
    global activeShortcut, lastRejectedShortcut
    if (nextShortcut = activeShortcut)
        return true

    previousShortcut := activeShortcut
    if (previousShortcut != '')
        Hotkey(previousShortcut, 'Off')

    try {
        if (nextShortcut != '')
            Hotkey(nextShortcut, ReadSelection, 'On')
        activeShortcut := nextShortcut
        lastRejectedShortcut := ''
        if notify {
            if (nextShortcut = '')
                TrayTip 'Atalho de leitura desativado.', 'Voz Local'
            else
                TrayTip 'Atalho de leitura atualizado.', 'Voz Local'
        }
        return true
    } catch as e {
        lastRejectedShortcut := nextShortcut
        if (previousShortcut != '') {
            try Hotkey(previousShortcut, ReadSelection, 'On')
        }
        TrayTip 'Não foi possível ativar o novo atalho. A combinação anterior foi mantida. ' e.Message, 'Voz Local'
        return false
    }
}

ReadSelection(*) {
    saved := ClipboardAll()
    A_Clipboard := ''
    Send '^c'
    if !ClipWait(1.5) {
        A_Clipboard := saved
        TrayTip 'Selecione um texto antes de usar o atalho de leitura.', 'Voz Local'
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
        request := ComObject('WinHttp.WinHttpRequest.5.1')
        request.SetTimeouts(2000, 2000, 5000, 120000)
        request.Open('POST', 'http://127.0.0.1:8888/tts', false)
        request.SetRequestHeader('Content-Type', 'application/json; charset=utf-8')
        request.Send(body)
        if request.Status != 200
            throw Error('Servidor retornou HTTP ' request.Status)
        path := A_Temp '\voz-local-leitura-' A_TickCount '.wav'
        file := ComObject('ADODB.Stream')
        file.Type := 1
        file.Open()
        file.Write(request.ResponseBody)
        file.SaveToFile(path, 2)
        file.Close()
        SoundPlay path, true
        FileDelete path
    } catch as e {
        TrayTip 'Não foi possível ler o texto: ' e.Message, 'Voz Local'
    }
}
