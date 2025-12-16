# 明日方舟干员数据查询 API

这是一个基于 FastAPI 的简单 API，用于查询和筛选《明日方舟》游戏中的干员数据。

数据源来自社区维护的 Git 仓库，且支持多数据源配置。

## 功能特性

-   **多数据源支持**: 可通过 `config.json` 轻松切换不同的游戏数据源 (例如 [Kengou/arknights-game-data](https://github.com/Kengou/arknights-game-data) 或 [Logical-Byte/arknights-game-data](https://github.com/Logical-Byte/arknights-game-data))。
-   **多条件筛选**: 支持通过名称（模糊搜索）、稀有度、职业、分支、位置、标签、势力、性别、出身地和获取途径等多种属性筛选干员。
-   **自动更新**: API 会在后台每小时自动从配置的数据源仓库拉取最新的游戏数据，无需手动更新。
-   **交互式文档**: 提供了两种 API 文档：
    -   详细的 [API 文档 (API_DOCUMENTATION.md)](API_DOCUMENTATION.md)。
    -   通过 FastAPI 自动生成的交互式 Swagger UI 文档，访问 `http://127.0.0.1:8000/docs` 即可使用。

## 环境要求

-   Python 3.10+
-   Git

## 安装与设置

1.  **克隆本项目**
    ```bash
    git clone <本项目仓库地址>
    cd <项目目录>
    ```

2.  **创建并激活 Python 虚拟环境**
    -   Windows (PowerShell):
        ```powershell
        python -m venv .venv
        .\.venv\Scripts\Activate.ps1
        ```
    -   macOS/Linux:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3.  **安装依赖**
    在激活虚拟环境后，运行以下命令安装所有必需的 Python 包：
    ```bash
    pip install -r requirements.txt
    ```

## 配置

本项目通过 `config.json` 文件来管理数据源。

```json
{
  "active_source": "Logical-Byte",
  "sources": {
    "Kengou": {
      "url": "https://github.com/Kengxxiao/ArknightsGameData.git",
      "path": "arknights-game-data-kengxxiao"
    },
    "Logical-Byte": {
      "url": "https://github.com/Logical-Byte/arknights-game-data.git",
      "path": "arknights-game-data-logical-byte"
    }
  },
  "update_interval_seconds": 3600
}
```

-   **切换数据源**:
    -   要切换数据源，请修改 `active_source` 的值。例如，要使用 `Logical-Byte` 的数据，请将其更改为:
        ```json
        "active_source": "Logical-Byte"
        ```
-   **首次运行**:
    -   当您第一次启动 API 时，程序会自动检查 `active_source` 对应的 `path` 是否存在。如果不存在，它将自动从相应的 `url` 克隆数据仓库。
-   **更新间隔**:
    -   `update_interval_seconds` 控制后台自动检查更新的频率（以秒为单位）。

## 如何运行

完成安装与设置后，在项目根目录下运行以下命令启动 API 服务：

```bash
uvicorn main:app --reload
```

服务启动后，您将在终端看到以下信息：
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
API 现在已在 `http://127.0.0.1:8000` 上运行。

## API 文档

有关如何使用 API 端点、参数和查看示例的详细信息，请参阅：

-   **[API 调用文档 (API_DOCUMENTATION.md)](API_DOCUMENTATION.md)**
-   或者，在 API 运行时访问交互式文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
