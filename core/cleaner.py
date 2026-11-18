"""
安全清理执行器与系统命令调度 (Safe Cleaner & System Dispatcher)
封装对 APFS 快照销毁、缓存文件清空、访达定位等动作的底层调用。
"""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Tuple

class SafeCleaner:
    
    @staticmethod
    def reveal_in_finder(path: str) -> bool:
        """在 macOS 访达 (Finder) 中高亮打开文件或目录"""
        expanded = os.path.expanduser(path)
        if not os.path.exists(expanded):
            # 若不存在则打开上一级目录
            expanded = os.path.dirname(expanded)
            
        if sys.platform == "darwin":
            try:
                subprocess.run(["open", "-R", expanded], check=False)
                return True
            except Exception:
                try:
                    subprocess.run(["open", expanded], check=False)
                    return True
                except Exception:
                    return False
        elif sys.platform == "win32":
            subprocess.run(["explorer", f"/select,{expanded}"], check=False)
            return True
        else:
            subprocess.run(["xdg-open", expanded], check=False)
            return True

    @staticmethod
    def purge_directory_contents(target_dir: str) -> Tuple[bool, int, str]:
        """
        安全清空指定目录内的所有文件与子目录（保留目录本身）
        返回: (是否成功, 释放的大致字节数, 错误信息)
        """
        expanded = os.path.expanduser(target_dir)
        if not os.path.exists(expanded):
            return True, 0, "目录已不存在，无需清理"

        total_freed = 0
        try:
            for root, dirs, files in os.walk(expanded):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        total_freed += os.path.getsize(fp)
                    except OSError:
                        pass

            # 删除内容
            for item in os.listdir(expanded):
                item_path = os.path.join(expanded, item)
                try:
                    if os.path.islink(item_path) or os.path.isfile(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                except Exception as e:
                    pass

            return True, total_freed, ""
        except Exception as e:
            return False, 0, str(e)

    @staticmethod
    def delete_apfs_local_snapshots() -> Tuple[bool, str]:
        """
        销毁 macOS APFS 本地时间机器快照 (需 tmutil)
        """
        if sys.platform != "darwin":
            return False, "当前非 macOS 系统，不支持 APFS 快照"

        try:
            # 列出快照
            res = subprocess.run(["tmutil", "listlocalsnapshots", "/"], capture_output=True, text=True)
            output = res.stdout
            
            # 查找形如 com.apple.TimeMachine.2026-11-18-164012.local 的快照
            lines = [line.strip() for line in output.splitlines() if "com.apple.TimeMachine" in line]
            if not lines:
                return True, "未检测到活跃的 APFS 本地快照"

            freed_count = 0
            for line in lines:
                # 提取日期标记
                parts = line.split(".")
                if len(parts) >= 4:
                    date_token = parts[3]
                    del_res = subprocess.run(["tmutil", "deletelocalsnapshots", date_token], capture_output=True, text=True)
                    if del_res.returncode == 0:
                        freed_count += 1

            return True, f"已成功销毁 {freed_count} 个 APFS 本地快照！"
        except Exception as e:
            return False, f"执行 tmutil 出错: {str(e)}"
