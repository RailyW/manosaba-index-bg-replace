import os
import shutil
import sys
import tempfile
from pathlib import Path

import UnityPy


REL_STILLS_PATH = Path(
    "manosaba_Data/StreamingAssets/aa/StandaloneWindows64/"
    "naninovel-backgrounds_assets_naninovel/backgrounds/stills"
)


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
    print("\n请选择首页背景人物：")
    print("  1) 艾玛（把 1_1.bundle 的背景写入 2_1.bundle 内部资源）")
    print("  2) 希罗（从 2_1.bundle.backup 恢复 2_1.bundle）")
    while True:
        c = input("> ").strip().lower()
        if c in {"1", "艾玛", "emma", "a"}:
            return "emma"
        if c in {"2", "希罗", "shiro", "s"}:
            return "shiro"
        print("输入无效，请输入 1/2（或 艾玛/希罗）。")


def validate_bundle_paths(stills_dir: Path) -> tuple[Path, Path, Path]:
    p_1_1 = stills_dir / "1_1.bundle"
    p_2_1 = stills_dir / "2_1.bundle"
    p_2_1_backup = stills_dir / "2_1.bundle.backup"

    if not p_1_1.exists():
        raise FileNotFoundError(f"未找到文件：{p_1_1}")
    if not p_2_1.exists():
        raise FileNotFoundError(f"未找到文件：{p_2_1}")

    return p_1_1, p_2_1, p_2_1_backup


def get_texture2d_objects(env) -> list:
    result = []
    for obj in env.objects:
        tname = getattr(obj.type, "name", "")
        if tname == "Texture2D":
            result.append(obj)
    return result


def replace_texture_inside_bundle(src_bundle: Path, dst_bundle: Path) -> None:
    src_env = UnityPy.load(str(src_bundle))
    dst_env = UnityPy.load(str(dst_bundle))

    src_textures = get_texture2d_objects(src_env)
    dst_textures = get_texture2d_objects(dst_env)

    if not src_textures:
        raise RuntimeError(f"源 bundle 未找到 Texture2D：{src_bundle}")
    if not dst_textures:
        raise RuntimeError(f"目标 bundle 未找到 Texture2D：{dst_bundle}")

    # 当前这两个 bundle 实测只有 1 个 Texture2D；这里保留兼容，若有多个则复制到所有目标 Texture2D。
    src_data = src_textures[0].read()
    src_image = src_data.image
    if src_image is None:
        raise RuntimeError("源 Texture2D 图像为空，无法替换。")

    for obj in dst_textures:
        data = obj.read()
        data.image = src_image.copy()
        data.save()

    # 原子写回，避免中途失败破坏文件
    out_data = dst_env.file.save()
    tmp_fd, tmp_name = tempfile.mkstemp(prefix="2_1.bundle.", suffix=".tmp", dir=str(dst_bundle.parent))
    try:
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(out_data)
        os.replace(tmp_name, dst_bundle)
    except Exception:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def apply_emma(p_1_1: Path, p_2_1: Path, p_2_1_backup: Path) -> None:
    if not p_2_1_backup.exists():
        shutil.copy2(p_2_1, p_2_1_backup)
        print(f"已创建备份：{p_2_1_backup}")
    else:
        print(f"检测到已存在备份，跳过覆盖：{p_2_1_backup}")

    replace_texture_inside_bundle(p_1_1, p_2_1)
    print("已完成：将艾玛背景写入 2_1.bundle（仅替换内部 Texture2D 资源）。")


def apply_shiro(p_2_1: Path, p_2_1_backup: Path) -> None:
    if not p_2_1_backup.exists():
        print("未找到 2_1.bundle.backup。")
        print("当前游戏文件并未发生过替换，二周目首页人物本身即为希罗，无需替换。")
        return

    shutil.copy2(p_2_1_backup, p_2_1)
    print("已恢复：2_1.bundle <- 2_1.bundle.backup（希罗背景）。")


def main() -> int:
    try:
        root = prompt_game_root()
        stills_dir = root / REL_STILLS_PATH

        if not stills_dir.exists() or not stills_dir.is_dir():
            raise FileNotFoundError(f"目标目录不存在：{stills_dir}")

        p_1_1, p_2_1, p_2_1_backup = validate_bundle_paths(stills_dir)

        print(f"\n目标目录：{stills_dir}")
        print(f"找到：{p_1_1.name}, {p_2_1.name}")

        choice = prompt_choice()
        if choice == "emma":
            apply_emma(p_1_1, p_2_1, p_2_1_backup)
        else:
            apply_shiro(p_2_1, p_2_1_backup)

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
