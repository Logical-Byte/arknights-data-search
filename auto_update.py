import time
import subprocess
import sys
import os

# 配置检查间隔（秒）
CHECK_INTERVAL = 60

def run_command(command, show_output=False):
    """运行 Shell 命令并返回输出"""
    try:
        result = subprocess.run(
            command, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            shell=True
        )
        if show_output and result.stdout:
            print(result.stdout)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # 即使失败也返回 None，不抛出异常
        return None

def get_file_hash(filepath):
    """获取文件的简单哈希（用于检测变更）"""
    if not os.path.exists(filepath):
        return None
    return run_command(f"git hash-object {filepath}")

def ensure_safe_directory():
    """解决 Linux/Docker 下 fatal: detected dubious ownership 错误"""
    try:
        current_dir = os.getcwd().replace("\\", "/")
        # 将当前目录标记为安全目录
        subprocess.run(
            f"git config --global --add safe.directory {current_dir}", 
            shell=True, 
            capture_output=True
        )
    except Exception:
        pass

def check_and_update(verbose=False):
    """检查并执行更新"""
    if verbose:
        print(f"[{time.strftime('%H:%M:%S')}] Checking for git updates...")
    
    # 确保目录安全
    ensure_safe_directory()
    
    # 1. 获取远程最新状态
    if run_command("git fetch") is None:
        return

    # 2. 获取本地和远程的 Commit Hash
    local_hash = run_command("git rev-parse HEAD")
    
    # 尝试获取当前分支名
    current_branch = run_command("git rev-parse --abbrev-ref HEAD")
    
    remote_hash = None
    if current_branch and current_branch != "HEAD":
        # 优先尝试标准上游
        remote_hash = run_command("git rev-parse @{u}")
        # 如果失败，且知道分支名，尝试 origin/分支名
        if not remote_hash:
            remote_hash = run_command(f"git rev-parse origin/{current_branch}")
    else:
        # Detached HEAD state? 尝试直接比较 origin/main 或 origin/master
        remote_hash = run_command("git rev-parse origin/main")
        if not remote_hash:
             remote_hash = run_command("git rev-parse origin/master")

    if not local_hash or not remote_hash:
        return

    # 3. 比较 Hash
    if local_hash != remote_hash:
        print(f"[{time.strftime('%H:%M:%S')}] Update found! Local: {local_hash[:7]} -> Remote: {remote_hash[:7]}")
        
        # 记录更新前 requirements.txt 的状态
        req_hash_before = get_file_hash("requirements.txt")
        
        # 4. 执行更新
        print("Pulling changes from git...")
        if current_branch == "HEAD":
             pull_output = run_command(f"git checkout {remote_hash}", show_output=True)
        else:
             pull_output = run_command("git pull", show_output=True)
        
        if pull_output is not None:
            print("Code updated successfully.")
            
            # 5. 检查是否需要更新依赖
            req_hash_after = get_file_hash("requirements.txt")
            if req_hash_before != req_hash_after:
                print("requirements.txt changed. Installing new dependencies...")
                python_exe = sys.executable
                run_command(f'"{python_exe}" -m pip install -r requirements.txt', show_output=True)
            
            print("Update process finished. Service should restart automatically via uvicorn reload.")
    elif verbose:
        print("Already up to date.")

def main():
    print(f"Auto-update script started. Monitoring git repository every {CHECK_INTERVAL} seconds.")
    ensure_safe_directory()
    try:
        while True:
            check_and_update()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nAuto-update script stopped.")

if __name__ == "__main__":
    main()