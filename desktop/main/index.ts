import {
  app,
  BrowserWindow,
  Menu,
  shell,
} from 'electron'
import { spawn, ChildProcess, execSync } from 'child_process'
import path from 'path'
import fs from 'fs'
import net from 'net'

// ── 全局变量 ──────────────────────────────────────────
let mainWindow: BrowserWindow | null = null
let backendProcess: ChildProcess | null = null

const isDev = !app.isPackaged

// ── 路径工具 ──────────────────────────────────────────
/** 获取项目根目录（开发模式）或 resources 目录（生产模式） */
function getProjectRoot(): string {
  if (isDev) {
    // __dirname = desktop/dist/main/
    // 需要三级 ../ 才能到达项目根目录
    return path.resolve(__dirname, '../../../')
  }
  return process.resourcesPath
}

/** 获取应用图标路径 */
function getAppIconPath(): string | undefined {
  if (process.platform === 'win32') {
    return path.join(__dirname, '../resources/icons/icon.ico')
  }
  if (process.platform === 'darwin') {
    return path.join(__dirname, '../resources/icons/icon.icns')
  }
  return undefined
}

// ── Python 环境检测 ──────────────────────────────────
/**
 * 在项目根目录下查找 Python 虚拟环境可执行文件。
 * 按常见虚拟环境目录名依次检查：.venv, venv, env, .env, _env
 * 如果找到，返回虚拟环境中的 python 路径；否则返回 null
 */
function findPythonExecutable(projectRoot: string): string | null {
  // 常见的虚拟环境目录名
  const venvDirs = ['.venv', 'venv', 'env', '.env', '_env']
  const isWindows = process.platform === 'win32'

  console.log(`[main] 正在检测 Python 虚拟环境，根目录: ${projectRoot}`)
  console.log(`[main] __dirname: ${__dirname}`)

  for (const dirName of venvDirs) {
    const dirPath = path.join(projectRoot, dirName)
    let pythonPath: string

    if (isWindows) {
      // Windows: <venv>/Scripts/python.exe
      pythonPath = path.join(dirPath, 'Scripts', 'python.exe')
      const dirExists = fs.existsSync(dirPath)
      const pythonExists = fs.existsSync(pythonPath)
      console.log(`[main] 检查 ${dirName}: 目录存在=${dirExists}, python存在=${pythonExists}`)
    } else {
      // macOS/Linux: <venv>/bin/python 或 python3
      pythonPath = path.join(dirPath, 'bin', 'python')
      const python3Path = path.join(dirPath, 'bin', 'python3')
      const dirExists = fs.existsSync(dirPath)
      const python3Exists = fs.existsSync(python3Path)
      console.log(`[main] 检查 ${dirName}: 目录存在=${dirExists}, python3存在=${python3Exists}`)
      
      if (fs.existsSync(python3Path)) {
        console.log(`[main] 找到 Python 虚拟环境: ${dirName}/bin/python3`)
        return python3Path
      }
    }

    if (fs.existsSync(pythonPath)) {
      console.log(`[main] 找到 Python 虚拟环境: ${dirName}${isWindows ? '/Scripts/python.exe' : '/bin/python'}`)
      return pythonPath
    }
  }

  // 未找到虚拟环境
  console.log('[main] 未检测到 Python 虚拟环境，使用系统 PATH 中的 python')
  return null
}

// ── 端口检测 ──────────────────────────────────────────
/** 检查指定端口是否已被占用 */
function checkPortInUse(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const server = net.createServer()
    server.once('error', () => resolve(true))
    server.once('listening', () => {
      server.close()
      resolve(false)
    })
    server.listen(port, '127.0.0.1')
  })
}

/**
 * 轮询等待指定端口可连接（TCP 连接成功即确认服务就绪）
 * @param port 目标端口
 * @param timeoutMs 超时时间（毫秒）
 * @param intervalMs 轮询间隔（毫秒）
 */
function waitForPort(port: number, timeoutMs = 30000, intervalMs = 300): Promise<void> {
  const start = Date.now()
  return new Promise((resolve, reject) => {
    const tryConnect = () => {
      const socket = new net.Socket()
      socket.setTimeout(500)
      socket.on('connect', () => {
        socket.destroy()
        console.log(`[main] 后端就绪（端口 ${port} 已可连接，耗时 ${Date.now() - start}ms）`)
        resolve()
      })
      socket.on('error', () => {
        socket.destroy()
        if (Date.now() - start >= timeoutMs) {
          reject(new Error(`等待端口 ${port} 超时（${timeoutMs}ms）`))
        } else {
          setTimeout(tryConnect, intervalMs)
        }
      })
      socket.on('timeout', () => {
        socket.destroy()
        if (Date.now() - start >= timeoutMs) {
          reject(new Error(`等待端口 ${port} 超时（${timeoutMs}ms）`))
        } else {
          setTimeout(tryConnect, intervalMs)
        }
      })
      socket.connect(port, '127.0.0.1')
    }
    tryConnect()
  })
}

// ── Python 后端启动 ──────────────────────────────────
async function startBackend(): Promise<void> {
  if (isDev) {
    // 开发模式：先检查端口 8000 是否已被占用
    const portInUse = await checkPortInUse(8000)
    if (portInUse) {
      console.log('[main] 检测到后端已在运行（端口 8000 已被占用），跳过自启动')
      return
    }

    // 端口空闲，启动后端
    const projectRoot = getProjectRoot()
    const pythonPath = findPythonExecutable(projectRoot)
    const pythonCmd = pythonPath || 'python'

    console.log(`[main] 启动 Python 后端（开发模式，使用: ${pythonCmd}）...`)
    
    const env = {
      ...process.env,
      OMNIHOME: app.getPath('userData'),
    }

    backendProcess = spawn(
      pythonCmd,
      [
        '-m', 'uvicorn', 'backend.main:app',
        '--host', '127.0.0.1',
        '--port', '8000',
      ],
      {
        cwd: projectRoot,
        env,
        stdio: ['ignore', 'pipe', 'pipe'],
      },
    )
  } else {
    // 生产模式：启动 PyInstaller 打包后的 exe
    const backendExe = path.join(
      process.resourcesPath,
      'backend',
      'backend.exe',
    )
    console.log('[main] 启动 Python 后端（生产模式）:', backendExe)
    const env = {
      ...process.env,
      OMNIHOME: app.getPath('userData'),
    }
    backendProcess = spawn(backendExe, [], {
      cwd: process.resourcesPath,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    })
  }

  // 日志输出
  backendProcess.stdout?.on('data', (data: Buffer) => {
    console.log(`[backend:stdout] ${data.toString().trim()}`)
  })
  backendProcess.stderr?.on('data', (data: Buffer) => {
    console.error(`[backend:stderr] ${data.toString().trim()}`)
  })
  backendProcess.on('error', (err: Error) => {
    console.error('[main] 后端进程启动失败:', err.message)
    console.log('[main] 提示：请确保 Python 已安装，或使用 `npm run dev:backend` 手动启动后端')
  })
  backendProcess.on('exit', (code: number | null, signal: string | null) => {
    console.log(`[main] 后端进程退出 (code=${code}, signal=${signal})`)
    backendProcess = null
  })

  // 等待后端 HTTP 服务就绪再返回
  try {
    await waitForPort(8000, 30000, 300)
  } catch (err) {
    console.error('[main]', (err as Error).message)
    console.log('[main] 提示：请确保 Python 后端依赖已安装（pip install -r requirements.txt）')
  }
}

/** 安全关闭后端子进程 */
function stopBackend(): void {
  if (backendProcess && !backendProcess.killed) {
    console.log('[main] 关闭后端子进程...')
    backendProcess.kill('SIGTERM')
    setTimeout(() => {
      if (backendProcess && !backendProcess.killed) {
        backendProcess.kill()
      }
    }, 3000)
  }
}

// ── 窗口创建 ──────────────────────────────────────────
function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    icon: getAppIconPath(),
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    show: false,
  })

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(
      path.join(__dirname, '../dist-frontend/index.html'),
    )
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show()
  })

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) {
      shell.openExternal(url)
    }
    return { action: 'deny' }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// ── 应用生命周期 ──────────────────────────────────────
app.whenReady().then(async () => {
  Menu.setApplicationMenu(null)

  // 启动 Python 后端（await 确保端口检测完成）
  await startBackend()

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  stopBackend()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  stopBackend()
})