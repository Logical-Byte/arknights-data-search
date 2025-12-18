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
        print(f"Error executing '{command}': {e.stderr}")
        return None

def get_file_hash(filepath):
    """获取文件的简单哈希（用于检测变更）"""
    if not os.path.exists(filepath):
        return None
    # 在 Windows 上使用简单的读取，或者使用 git hash-object
    return run_command(f"git hash-object {filepath}")

def check_and_update(verbose=False):
    """检查并执行更新"""
    if verbose:
        print(f"[{time.strftime('%H:%M:%S')}] Checking for git updates...")
    
    # 1. 获取远程最新状态
    if run_command("git fetch") is None:
        return

    # 2. 获取本地和远程的 Commit Hash
    local_hash = run_command("git rev-parse HEAD")
    # @{u} 代表当前分支的上游分支（如 origin/main）
    remote_hash = run_command("git rev-parse @{u}")

    if not local_hash or not remote_hash:
        if verbose:
            print("Warning: Could not determine git hashes. Ensure this branch tracks a remote branch.")
        return

    # 3. 比较 Hash
    if local_hash != remote_hash:
        print(f"[{time.strftime('%H:%M:%S')}] Update found! Local: {local_hash[:7]} -> Remote: {remote_hash[:7]}")
        
        # 记录更新前 requirements.txt 的状态
        req_hash_before = get_file_hash("requirements.txt")
        
        # 4. 执行更新
        print("Pulling changes from git...")
        pull_output = run_command("git pull", show_output=True)
        
        if pull_output:
            print("Code updated successfully.")
            
            # 5. 检查是否需要更新依赖
            req_hash_after = get_file_hash("requirements.txt")
            if req_hash_before != req_hash_after:
                print("requirements.txt changed. Installing new dependencies...")
                # 使用当前环境的 pip
                python_exe = sys.executable
                run_command(f"\"{python_exe}\" -m pip install -r requirements.txt", show_output=True)
            
            print("Update process finished. Service should restart automatically via uvicorn reload.")
    elif verbose:
        print("Already up to date.")

def main():
    print(f"Auto-update script started. Monitoring git repository every {CHECK_INTERVAL} seconds.")
    try:
        while True:
            check_and_update()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nAuto-update script stopped.")

if __name__ == "__main__":
    main()
