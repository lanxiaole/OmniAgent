# 配置管理模块（公共入口 / 兼容层）
#
# 设计原则：
#   1. 所有可通过设置页面 UI 修改的配置 → 存放在项目根目录 .env 文件中，
#      通过 getter 函数动态读取，保存后即时生效，无需重启。
#   2. 所有不可通过设置页面修改的配置 → 硬编码为模块级常量。
#   3. 目录/路径相关配置 → 硬编码为模块级常量。
#   4. .env 读写工具函数 → 保留在本文件中，供设置页面 API 使用。
#
# 新克隆项目时无需手动创建 .env 文件，启动后通过设置页面配置即可
# 自动生成 .env。
#
# 说明：为避免单个文件职责过重，配置逻辑已拆分为独立子模块，本文件
#       仅作为向后兼容的聚合入口，统一 re-export 各子模块命名，
#       因此既有 `from agent_core.config.settings import ...` 无需改动。

# 按依赖顺序导入各子模块（paths 最底层，scenarios 依赖 paths）
from agent_core.config.paths import *          # noqa: F401, F403 - exps
from agent_core.config.env import *            # noqa: F401, F403
from agent_core.config.constants import *      # noqa: F401, F403
from agent_core.config.scenarios import *      # noqa: F401, F403