import { contextBridge, shell, app } from 'electron'

/**
 * 通过 contextBridge 安全地向渲染进程暴露系统 API。
 * 渲染进程通过 window.electronAPI 访问这些方法。
 */
contextBridge.exposeInMainWorld('electronAPI', {
  /** 在文件管理器中打开指定路径 */
  openPath: (path: string) => shell.openPath(path),

  /** 获取应用版本号 */
  getVersion: () => app.getVersion(),

  /** 当前操作系统平台 */
  platform: process.platform,
})