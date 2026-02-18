# manosaba-index-bg-replace

《魔法少女的魔女审判》首页背景切换工具。

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
   - `1` / `艾玛`
   - `2` / `希罗`

---

## 变更规则

脚本会修改并备份这个文件：

```text
manosaba_game\manosaba_Data\StreamingAssets\aa\StandaloneWindows64\naninovel-scripts_assets_naninovelscripts-system.bundle
```

- 第一次选择“艾玛”时，脚本会先备份：
  - `naninovel-scripts_assets_naninovelscripts-system.bundle`
  - `-> naninovel-scripts_assets_naninovelscripts-system.bundle.backup`
- 如果备份已存在，脚本会**跳过覆盖**，确保历史原始备份不被重复改写。

当你选择“希罗”时：
- 若存在 `.backup`，会恢复原脚本 bundle。
- 若不存在备份，会提示当前未发生过替换，标题本身即按原始逻辑显示。

---


## Q&A

### Q1：提示找不到目录/文件？
请确认你输入的是**游戏根目录**（`manosaba_game`），而不是更深层目录。

### Q2：脚本会修改哪个文件？

```text
manosaba_game\manosaba_Data\StreamingAssets\aa\StandaloneWindows64\naninovel-scripts_assets_naninovelscripts-system.bundle
```
