import uvicorn
import threading
import time
from auto_update import check_and_update, CHECK_INTERVAL

def update_worker():
    """后台更新工作线程"""
    print("Auto-update background worker started.")
    while True:
        try:
            check_and_update()
        except Exception as e:
            print(f"Auto-update error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # 启动后台自动更新线程 (daemon=True 确保主程序退出时线程也随之停止)
    update_thread = threading.Thread(target=update_worker, daemon=True)
    update_thread.start()
    
    # 运行 API 服务
    # 注意：reload=True 配合 git pull 会在代码拉取后自动重启服务
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
