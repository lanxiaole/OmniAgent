# uv包管理器部署问题

**setuptools 的 flat-layout 自动发现限制**

当你没有显式声明 `packages` 时，setuptools 会扫描项目根目录，自动把含有 `.py` 文件或子目录的文件夹识别为候选 Python 包。你的根目录下同时存在 `agent_core`、`backend`、`frontend`、`assets`、`docker`，setuptools 发现了多个"看起来像包"的顶级目录。

但 **flat-layout（扁平布局）不允许自动发现多个顶级包** —— 这是 setuptools 的安全机制，防止误把 `tests/`、`docs/`、`assets/` 这类非包目录打包进发布版本。所以它会直接抛错退出。

**解决方案**：显式告诉 setuptools 哪些是你要打包的包，哪些不是。即通过 `[tool.setuptools]` 段声明 `packages` 和 `py-modules`。