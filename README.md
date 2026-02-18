# manosaba-index-bg-replace

《魔法少女的魔女审判》首页背景切换工具。

它的作用是：
- 在**不直接整文件替换 bundle** 的前提下，修改 `2_1.bundle` 内部的背景贴图资源；
- 在二周目时，也可以显示一周目的首页背景（艾玛）；
- 支持恢复回原本的二周目背景（希罗）。

---

## 运行前准备

### 1) Python 环境
建议 Python 3.10+。

### 2) 安装依赖

```bash
pip install -r requirement.txt
```

---

## 如何使用

在项目目录运行：

```bash
python replace_bg.py
```

脚本会按提示执行：

1. 输入游戏根目录，例如：

```text
E:\game\steam\steamapps\common\manosaba_game
```

2. 选择背景人物：
   - `1` / `艾玛`：将 `1_1.bundle` 的背景贴图写入 `2_1.bundle`
   - `2` / `希罗`：从备份恢复 `2_1.bundle`

---

## 备份与恢复规则（很重要）

- 第一次选择“艾玛”时，脚本会先备份：
  - `2_1.bundle` → `2_1.bundle.backup`
- 如果已经存在 `2_1.bundle.backup`，脚本会**跳过备份，不会覆盖旧备份**。

当你选择“希罗”时：
- 若存在 `2_1.bundle.backup`，会恢复到 `2_1.bundle`。
- 若不存在备份，会提示：当前未发生过替换，二周目本身就是希罗，无需替换。

---


## Q&A

### Q1：提示找不到目录/文件？
请确认你输入的是**游戏根目录**（`manosaba_game`），而不是更深层目录。

### Q2：游戏文件保存在？

```bash
manosaba_game\manosaba_Data\StreamingAssets\aa\StandaloneWindows64\naninovel-backgrounds_assets_naninovel\backgrounds\stills
```
