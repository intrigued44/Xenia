const { app, BrowserWindow, ipcMain } = require('electron')
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
        const serverPath = path.join(
            process.resourcesPath,
            'xenia_server',
            process.platform === 'win32'
                ? 'xenia_server.exe'
                : 'xenia_server'
        )
        return serverPath
    }
    return null
}

function getReadyFilePath() {
    if (app.isPackaged) {
        return path.join(
            process.resourcesPath,
            'xenia_server',
            '.xenia_ready'
        )
    }
    return path.join(__dirname, '..', '.xenia_ready')
}

function startServer() {
    const serverPath = getServerExecutable()
    if (!serverPath || !fs.existsSync(serverPath)) {
        console.log('Dev mode: expecting server already running')
        return
    }
    
    serverProcess = spawn(serverPath, [], {
        detached: false,
        stdio: 'ignore',
        windowsHide: true
    })
    
    serverProcess.on('error', (err) => {
        console.error('Server failed to start:', err)
    })
}

function waitForReady(maxAttempts = 30) {
    return new Promise((resolve) => {
        let attempts = 0
        const readyFile = getReadyFilePath()
        
        const check = setInterval(() => {
            attempts++
            
            // Check ready file first (faster)
            if (fs.existsSync(readyFile)) {
                clearInterval(check)
                resolve(true)
                return
            }
            
            // Also ping health endpoint
            http.get(
                `${API_BASE}/v1/health`,
                (res) => {
                    if (res.statusCode === 200) {
                        clearInterval(check)
                        resolve(true)
                    }
                }
            ).on('error', () => {})
            
            if (attempts >= maxAttempts) {
                clearInterval(check)
                resolve(false)
            }
        }, 1000)
    })
}

function isFirstRun() {
    const configPath = path.join(
        app.getPath('userData'),
        'xenia_config.json'
    )
    return !fs.existsSync(configPath)
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 820,
        minWidth: 900,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        title: 'Xenia',
        show: false,
        backgroundColor: '#f8fafc'
    })
    
    // Show loading first
    mainWindow.loadFile(
        path.join(__dirname, 'loading.html')
    )
    mainWindow.show()
    
    return mainWindow
}

app.whenReady().then(async () => {
    createWindow()
    startServer()
    
    const ready = await waitForReady(40)
    
    if (!ready) {
        mainWindow.loadURL(
            'data:text/html,' + encodeURIComponent(`
            <html>
            <body style="font-family:system-ui;
                         display:flex;
                         align-items:center;
                         justify-content:center;
                         height:100vh;
                         margin:0;
                         background:#f8fafc">
            <div style="text-align:center">
                <h2 style="color:#ef4444">
                    Could not start Xenia
                </h2>
                <p style="color:#64748b">
                    Please restart the application.
                </p>
                <button onclick="window.close()"
                    style="padding:8px 16px;
                           margin-top:16px;
                           cursor:pointer">
                    Close
                </button>
            </div>
            </body></html>
            `)
        )
        return
    }
    
    // Check first run
    if (isFirstRun()) {
        mainWindow.loadFile(
            path.join(__dirname, 'setup.html')
        )
    } else {
        mainWindow.loadFile(
            path.join(__dirname, 'index.html')
        )
    }
    
    ipcMain.on('setup-complete', (event, config) => {
        const configPath = path.join(app.getPath('userData'), 'xenia_config.json')
        fs.writeFileSync(configPath, JSON.stringify(config))
    })
})

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})

app.on('before-quit', () => {
    if (serverProcess) {
        serverProcess.kill()
    }
    // Clean up ready file
    const readyFile = getReadyFilePath()
    if (fs.existsSync(readyFile)) {
        fs.unlinkSync(readyFile)
    }
})

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow()
    }
})
