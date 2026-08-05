/**
 * 构建辅助脚本：调用 PyInstaller 打包 Python 后端。
 *
 * 用法: node scripts/build-backend.js
 *
 * 确保 backend/backend.spec 已存在，否则运行会失败。
 */
const { execSync } = require('child_process')
const path = require('path')

const backendDir = path.resolve(__dirname, '../../backend')

console.log('[build-backend] 开始打包 Python 后端...')
console.log(`[build-backend] 后端目录: ${backendDir}`)

try {
  execSync('pyinstaller backend.spec --clean', {
    cwd: backendDir,
    stdio: 'inherit',
  })
  console.log('[build-backend] Python 后端打包完成')
} catch (err) {
  console.error('[build-backend] 打包失败:', err.message)
  process.exit(1)
}