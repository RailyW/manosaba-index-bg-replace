import os
import stat
import shutil
import sys
import tempfile
from pathlib import Path

import UnityPy


REL_AA_PATH = Path("manosaba_Data/StreamingAssets/aa/StandaloneWindows64")
SCRIPT_BUNDLE_NAME = "naninovel-scripts_assets_naninovelscripts-system.bundle"
SCRIPT_CONTAINER_SUFFIX = "Assets/#WitchTrials/Scenarios/System/System_Title.nani"

# 标题脚本中原始表达式：一周目显示 1_1，二周目显示 2_1
SHIRO_EXPR = 'g_gameProgress < 6 ? "1_1" : "2_1"'
# 固定艾玛标题背景
EMMA_EXPR = '"1_1"'


def prompt_game_root() -> Path:
    raw = input("请输入游戏根目录（例如 E:\\game\\steam\\steamapps\\common\\manosaba_game）：\n> ").strip()
    raw = raw.strip('"').strip("'")
    if not raw:
        raise ValueError("未输入游戏根目录。")

    root = Path(raw)
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"目录不存在：{root}")
    return root


def prompt_choice() -> str:
    print("\n请选择标题背景人物：")
    print("  1) 艾玛（仅改标题脚本表达式，不改 2_1.bundle 图像）")
    print("  2) 希罗（恢复标题脚本 bundle 备份）")
    while True:
        c = input("> ").strip().lower()
        if c in {"1", "艾玛", "emma", "a"}:
            return "emma"
        if c in {"2", "希罗", "shiro", "s"}:
            return "shiro"
        print("输入无效，请输入 1/2（或 艾玛/希罗）。")


def validate_paths(game_root: Path) -> tuple[Path, Path]:
    aa_dir = game_root / REL_AA_PATH
    if not aa_dir.exists() or not aa_dir.is_dir():
        raise FileNotFoundError(f"目标目录不存在：{aa_dir}")

    script_bundle = aa_dir / SCRIPT_BUNDLE_NAME
    script_backup = aa_dir / f"{SCRIPT_BUNDLE_NAME}.backup"
    if not script_bundle.exists():
        raise FileNotFoundError(f"未找到文件：{script_bundle}")

    return script_bundle, script_backup


def get_title_script_reader(env):
    pptr = None
    for key, obj in env.container.items():
        if key.endswith(SCRIPT_CONTAINER_SUFFIX):
            pptr = obj
            break

    if pptr is None:
        raise RuntimeError(f"未在 bundle container 中找到：{SCRIPT_CONTAINER_SUFFIX}")

    for reader in env.objects:
        if getattr(reader, "path_id", None) == pptr.path_id:
            return reader

    raise RuntimeError("未找到 System_Title.nani 对应的对象读取器。")


def patch_title_expression(script_bundle: Path, mode: str) -> int:
    env = UnityPy.load(str(script_bundle))
    reader = get_title_script_reader(env)
    tree = reader.read_typetree()

    refs = tree.get("references", {}).get("RefIds", [])
    if not refs:
        raise RuntimeError("System_Title.nani 中未找到 references.RefIds，结构可能不兼容。")

    if mode == "emma":
        target_expr = EMMA_EXPR
    elif mode == "shiro":
        target_expr = SHIRO_EXPR
    else:
        raise ValueError(f"未知模式：{mode}")

    changed = 0
    for ref in refs:
        cls = ref.get("type", {}).get("class", "")
        if cls != "ModifyBackgroundExtended":
            continue

        data = ref.get("data", {})
        at = data.get("AppearanceAndTransition", {})
        raw = at.get("raw", {})
        parts = raw.get("parts", [])
        if not parts:
            continue

        part0 = parts[0]
        expr = str(part0.get("expression", "")).strip()
        # 只改与标题背景选择相关的那两条动态表达式
        if "g_gameProgress" in expr and '"1_1"' in expr and '"2_1"' in expr:
            if expr != target_expr:
                part0["expression"] = target_expr
                changed += 1

    if changed == 0 and mode == "emma":
        raise RuntimeError("未找到可改写为艾玛的目标表达式，可能已被改动或游戏版本结构不同。")

    # 写回 typetree 并保存 bundle
    reader.save_typetree(tree)
    out_data = env.file.save()

    tmp_fd, tmp_name = tempfile.mkstemp(prefix=f"{SCRIPT_BUNDLE_NAME}.", suffix=".tmp", dir=str(script_bundle.parent))
    try:
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(out_data)

        # 某些环境下目标文件可能是只读，先尝试解除只读属性
        if script_bundle.exists():
            try:
                os.chmod(script_bundle, stat.S_IWRITE)
            except Exception:
                pass

        os.replace(tmp_name, script_bundle)
    except PermissionError as e:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise RuntimeError(
            "写入失败（拒绝访问）。请先关闭游戏进程和可能占用该文件的程序后重试；"
            "若仍失败，请以管理员权限运行终端再执行脚本。"
        ) from e
    except Exception:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise

    return changed


def apply_emma(script_bundle: Path, script_backup: Path) -> None:
    if not script_backup.exists():
        shutil.copy2(script_bundle, script_backup)
        print(f"已创建备份：{script_backup}")
    else:
        print(f"检测到已存在备份，跳过覆盖：{script_backup}")

    changed = patch_title_expression(script_bundle, mode="emma")
    print(f"已完成：标题脚本中 {changed} 处表达式改为艾玛（\"1_1\"）。")
    print("说明：此方案不会改动 2_1.bundle 图像，因此不会影响 CG 鉴赏页面。")


def apply_shiro(script_bundle: Path, script_backup: Path) -> None:
    if not script_backup.exists():
        print(f"未找到 {script_backup.name}。")
        print("当前脚本文件未发生过替换，标题本身即按游戏进度显示希罗，无需恢复。")
        return

    shutil.copy2(script_backup, script_bundle)
    print(f"已恢复：{SCRIPT_BUNDLE_NAME} <- {script_backup.name}（希罗/原始逻辑）。")


def main() -> int:
    try:
        game_root = prompt_game_root()
        script_bundle, script_backup = validate_paths(game_root)

        print(f"\n目标脚本 bundle：{script_bundle}")
        choice = prompt_choice()

        if choice == "emma":
            apply_emma(script_bundle, script_backup)
        else:
            apply_shiro(script_bundle, script_backup)

        print("\n操作完成。")
        return 0
    except KeyboardInterrupt:
        print("\n用户取消操作。")
        return 1
    except Exception as e:
        print(f"\n发生错误：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
