const { app, BrowserWindow, ipcMain, screen } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const fs = require('fs')
const http = require('http')

let serverProcess = null
let mainWindow = null
const PORT = 8000
const API_BASE = `http://127.0.0.1:${PORT}`

function getServerExecutable() {
    if (app.isPackaged) {
        return path.join(
            process.resourcesPath,
            'xenia_server',
            process.platform === 'win32' ? 'xenia_server.exe' : 'xenia_server'
        )
    }
    return null
}

function startServer() {
    const serverPath = getServerExecutable()
    if (!serverPath || !fs.existsSync(serverPath)) {
        console.log('[Xenia] Dev mode — expecting server on port 8000')
        return
    }
    console.log('[Xenia] Starting bundled server:', serverPath)
    serverProcess = spawn(serverPath, [], {
        detached: false,
        stdio: 'ignore',
        windowsHide: true,
        cwd: path.dirname(serverPath)
    })
    serverProcess.on('error', (err) => console.error('[Xenia] Server spawn error:', err))
    serverProcess.on('exit', (code) => console.log('[Xenia] Server exited with code:', code))
}

function pingHealth() {
    return new Promise((resolve) => {
        try {
            const req = http.get(`${API_BASE}/v1/health`, (res) => {
                let data = ''
                res.on('data', d => data += d)
                res.on('end', () => resolve(res.statusCode === 200))
            })
            req.on('error', () => resolve(false))
            req.setTimeout(1200, () => { req.destroy(); resolve(false) })
        } catch (e) {
            resolve(false)
        }
    })
}

async function waitForServer(maxSeconds = 60) {
    for (let i = 0; i < maxSeconds; i++) {
        const ok = await pingHealth()
        if (ok) {
            console.log(`[Xenia] Server ready after ${i + 1}s`)
            return true
        }
        await new Promise(r => setTimeout(r, 1000))
    }
    console.warn('[Xenia] Server timeout — loading UI anyway')
    return false
}

function isSetupComplete() {
    const configPath = path.join(app.getPath('userData'), 'xenia_config.json')
    const exists = fs.existsSync(configPath)
    console.log('[Xenia] userData:', app.getPath('userData'), '| config exists:', exists)
    return exists
}

function markSetupComplete(config) {
    const configPath = path.join(app.getPath('userData'), 'xenia_config.json')
    const dir = path.dirname(configPath)
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
    fs.writeFileSync(configPath, JSON.stringify(config || {
        setup_complete: true,
        onboarding_complete: true,
        user_name: 'User',
        created_at: new Date().toISOString()
    }, null, 2))
}

function createWindow() {
    const primaryDisplay = screen.getPrimaryDisplay()
    const { width: sw, height: sh } = primaryDisplay.workAreaSize
    const winW = Math.min(1280, sw - 40)
    const winH = Math.min(860, sh - 40)
    const winX = Math.floor((sw - winW) / 2)
    const winY = Math.floor((sh - winH) / 2)

    console.log(`[Xenia] Creating window ${winW}x${winH} at (${winX},${winY}) on ${sw}x${sh} display`)

    mainWindow = new BrowserWindow({
        width: winW,
        height: winH,
        minWidth: 900,
        minHeight: 600,
        x: winX,
        y: winY,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        title: 'Xenia',
        show: true,   // Show immediately - don't hide
        frame: true,
        backgroundColor: '#0d0d0f'
    })

    mainWindow.webContents.on('did-fail-load', (e, code, desc, url) => {
        console.error(`[Xenia] Page load failed: ${desc} (${code}) for ${url}`)
    })

    mainWindow.webContents.on('render-process-gone', (e, details) => {
        console.error('[Xenia] Renderer gone:', details.reason, details.exitCode)
    })

    // Bring to front after a moment
    setTimeout(() => {
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.moveTop()
            mainWindow.focus()
        }
    }, 500)

    mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
        try {
            fs.appendFileSync('C:/Users/pranav/Downloads/nous-windows-installer-src/console_errors.txt', `[Console] Level ${level}: ${message} (${sourceId}:${line})\n`, 'utf8');
        } catch (e) {}
    });
    // mainWindow.webContents.openDevTools();

    return mainWindow;
}

app.whenReady().then(async () => {
    console.log('[Xenia] App ready, creating window...')
    const win = createWindow()
    win.loadFile(path.join(__dirname, 'loading.html'))

    startServer()
    await waitForServer(60)

    if (!mainWindow || mainWindow.isDestroyed()) {
        console.error('[Xenia] Main window was destroyed during startup!')
        return
    }

    if (isSetupComplete()) {
        console.log('[Xenia] Setup complete — loading index.html')
        mainWindow.loadFile(path.join(__dirname, 'index.html'))
    } else {
        console.log('[Xenia] First run — loading setup.html')
        mainWindow.loadFile(path.join(__dirname, 'setup.html'))
    }

    ipcMain.on('setup-complete', (event, config) => {
        console.log('[Xenia] Setup complete IPC received')
        markSetupComplete(config)
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.loadFile(path.join(__dirname, 'index.html'))
        }
    })
})

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
    if (serverProcess) {
        try { serverProcess.kill('SIGTERM') } catch (e) {}
    }
})

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
