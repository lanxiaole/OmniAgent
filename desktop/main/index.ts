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

// ── 残留进程清理工具 ──────────────────────────────────
/**
 * 清理可能残留的 backend 进程
 * 在应用启动前调用，确保没有旧进程占用端口或日志文件
 */
function cleanupStaleBackends(): void {
  try {
    const isWindows = process.platform === 'win32'
    if (isWindows) {
      // Windows: 使用 taskkill 清理残留的 backend.exe 进程
      try {
        const result = execSync(
          'tasklist /FI "IMAGENAME eq backend.exe" /NH',
          { encoding: 'utf-8', timeout: 5000 }
        )
        if (result && result.includes('backend.exe')) {
          console.log('[main] 发现残留的 backend 进程，正在清理...')
          execSync('taskkill /F /IM backend.exe /T', { encoding: 'utf-8', timeout: 5000 })
          console.log('[main] 残留进程已清理')
        }
      } catch (e) {
        // tasklist 可能找不到进程，这是正常的
      }
    } else {
      // macOS/Linux: 使用 pkill 清理
      try {
        execSync('pkill -f "backend.exe" 2>/dev/null || true', { encoding: 'utf-8', timeout: 5000 })
      } catch (e) {
        // 忽略错误
      }
    }
  } catch (err) {
    console.warn('[main] 清理残留进程时出错:', err)
  }
}

/**
 * 开发模式下：强制清理占用指定端口的进程（Windows 专用）
 * 通过 netstat 找到占用端口的 PID，然后用 taskkill 杀掉整个进程树
 */
function killPortProcessWindows(port: number): boolean {
  if (process.platform !== 'win32') return false

  try {
    // 查找占用端口的 PID
    const netstatOutput = execSync(
      `netstat -ano | findstr :${port}`,
      { encoding: 'utf-8', timeout: 5000 }
    )
    console.log(`[main] netstat ${port}:`, netstatOutput)

    // 提取所有 LISTENING 状态的 PID
    const lines = netstatOutput.split('\n').filter((l) => l.includes('LISTENING'))
    const pids = new Set<string>()
    for (const line of lines) {
      const parts = line.trim().split(/\s+/)
      const pid = parts[parts.length - 1]
      if (pid && /^\d+$/.test(pid)) {
        pids.add(pid)
      }
    }

    if (pids.size === 0) return false

    console.log(`[main] 发现占用端口 ${port} 的进程 PID: ${[...pids].join(', ')}，正在清理...`)
    for (const pid of pids) {
      try {
        execSync(`taskkill /F /PID ${pid} /T`, { encoding: 'utf-8', timeout: 5000 })
        console.log(`[main] 已终止进程 PID ${pid} (端口 ${port})`)
      } catch (e: any) {
        console.warn(`[main] 终止 PID ${pid} 时出错:`, e.message)
      }
    }
    return true
  } catch (e: any) {
    console.warn(`[main] 查找端口 ${port} 占用进程时出错:`, e.message)
    return false
  }
}

/**
 * 清理日志目录中可能被占用的旧日志文件
 */
function cleanupLogDir(): void {
  try {
    const logDir = path.join(app.getPath('userData'), 'workspace', 'logs')
    if (!fs.existsSync(logDir)) return
    
    // 清理所有 .log 文件
    const files = fs.readdirSync(logDir)
    let cleaned = 0
    for (const file of files) {
      if (file.endsWith('.log')) {
        try {
          fs.unlinkSync(path.join(logDir, file))
          cleaned++
        } catch (e) {
          // 文件可能被占用，跳过
          console.warn(`[main] 无法删除日志文件 ${file}，可能被占用`)
        }
      }
    }
    if (cleaned > 0) {
      console.log(`[main] 已清理 ${cleaned} 个旧日志文件`)
    }
  } catch (err) {
    console.warn('[main] 清理日志目录时出错:', err)
  }
}

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
  // 开发模式：项目内的 resources/icons/
  // 生产模式：打包后 resources/icons/（来自 extraResources）
  const iconDir = isDev
    ? path.resolve(__dirname, '../../resources/icons')
    : path.join(process.resourcesPath, 'icons')

  if (process.platform === 'win32') {
    const iconPath = path.join(iconDir, 'icon.ico')
    if (fs.existsSync(iconPath)) return iconPath
    return undefined
  }
  if (process.platform === 'darwin') {
    const iconPath = path.join(iconDir, 'icon.icns')
    if (fs.existsSync(iconPath)) return iconPath
    return undefined
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
  // 启动前清理残留进程和日志文件
  if (!isDev) {
    cleanupStaleBackends()
    cleanupLogDir()
    // 等待一小段时间让文件锁释放
    await new Promise((resolve) => setTimeout(resolve, 500))
  }

  if (isDev) {
    // 开发模式：先检查端口 8000 是否被旧进程占用
    const portInUse = await checkPortInUse(8000)
    if (portInUse) {
      console.log('[main] 检测到端口 8000 已被占用，尝试清理旧进程...')
      // 开发模式下强制清理旧进程，确保每次重启都使用最新代码
      if (process.platform === 'win32') {
        killPortProcessWindows(8000)
      } else {
        try {
          execSync('lsof -ti:8000 | xargs kill -9 2>/dev/null || true', { 
            encoding: 'utf-8', timeout: 5000 
          })
        } catch (e) {
          // 忽略错误
        }
      }
      // 等待端口释放
      await new Promise((resolve) => setTimeout(resolve, 1000))
      const stillInUse = await checkPortInUse(8000)
      if (stillInUse) {
        console.warn('[main] 无法释放端口 8000，将尝试继续使用该端口')
      } else {
        console.log('[main] 端口 8000 已释放')
      }
    }

    // 启动新的后端进程
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
  if (!backendProcess || backendProcess.killed) return
  console.log('[main] 关闭后端子进程... (PID:', backendProcess.pid, ')')

  // 存储 PID 以防 backendProcess 对象失效
  const pid = backendProcess.pid

  if (process.platform === 'win32') {
    // Windows: SIGTERM 不存在，直接用 taskkill 杀整个进程树
    try {
      execSync(`taskkill /F /PID ${pid} /T`, { encoding: 'utf-8', timeout: 10000 })
      console.log('[main] 后端进程树已终止')
    } catch (e: any) {
      console.warn('[main] taskkill 失败:', e.message)
    }
    backendProcess = null
    return
  }

  // macOS/Linux: 先优雅关闭
  backendProcess.kill('SIGTERM')

  // 设置超时强制关闭
  const forceKillTimer = setTimeout(() => {
    if (backendProcess && !backendProcess.killed) {
      console.log('[main] 优雅关闭超时，强制终止后端进程')
      backendProcess.kill('SIGKILL')
    }
  }, 3000)

  // 进程退出时清理定时器
  backendProcess.once('exit', () => {
    clearTimeout(forceKillTimer)
  })
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
  } else {
    // 生产模式：后端托管前端，走 HTTP 同源（API 直接可用）
    mainWindow.loadURL('http://localhost:8000')
  }

  // F12 / Ctrl+Shift+I 切换开发者工具（开发+生产均可用，方便排查空白屏）
  mainWindow.webContents.on('before-input-event', (_event, input) => {
    if (
      input.key === 'F12' ||
      (input.control && input.shift && input.key === 'I')
    ) {
      mainWindow?.webContents.toggleDevTools()
    }
  })

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