/**
 * 构建辅助脚本：将 frontend/dist/ 复制到 desktop/dist-frontend/
 * 以便 electron-builder 将其打包到安装包中。
 *
 * 在 build:electron 脚本中（tsc 编译后，electron-builder 前）调用。
 */
const fs = require('fs')
const path = require('path')

const srcDir = path.resolve(__dirname, '../../frontend/dist')
const destDir = path.resolve(__dirname, '../dist-frontend')

if (!fs.existsSync(srcDir)) {
  console.error(`[copy-frontend] 错误: 前端构建产物不存在: ${srcDir}`)
  console.error('[copy-frontend] 请先执行 npm run build:frontend')
  process.exit(1)
}

// 清空目标目录
if (fs.existsSync(destDir)) {
  fs.rmSync(destDir, { recursive: true })
}

// 复制（Node.js 16.7+ 支持 fs.cpSync）
fs.cpSync(srcDir, destDir, { recursive: true })
console.log(`[copy-frontend] 前端构建产物已复制到 ${destDir}`)