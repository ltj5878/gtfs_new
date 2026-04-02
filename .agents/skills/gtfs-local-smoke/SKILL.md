---
name: gtfs-local-smoke
description: 在 gtfs_new 仓库中启动、排查和验证项目本地环境时使用。适用于检查 PostgreSQL、后端 5001、前端 5173、start.sh、健康接口、脚本式 API smoke test、构建结果、日志定位，以及快速判断问题是环境、数据、接口还是页面接入造成的。
---

# GTFS Local Smoke

这个 skill 面向本地联调和快速验收，不是做功能大改。当前项目已经有较多页面和后台能力，很多问题首先要判断是环境、数据、权限还是前后端契约断了。

## 默认入口

- 全栈优先使用 `./start.sh start|stop|status|restart`。
- 后端单跑使用 `cd backend && python3 -m api.app`。
- 前端单跑使用 `cd frontend && npm run dev`。

## 项目约定

- PostgreSQL 是默认本地数据库。
- 后端默认端口 `5001`，前端默认端口 `5173`。
- `start.sh` 会把日志写到:
  - `/tmp/gtfs_backend.log`
  - `/tmp/gtfs_frontend.log`
- PID 文件也在 `/tmp`，排查假存活或端口占用时先看这些位置。

## 推荐排查顺序

1. 先看 `./start.sh status`，确认数据库、后端、前端是否都起来了。
2. 再看 `/api/health`，确认数据库连接不是假启动。
3. 再看基础和业务接口，例如 `/api/stats`、`/api/realtime/summary`、`/api/punctuality/overview`。
4. 如果接口正常但页面异常，再检查前端代理、登录态、路由守卫和权限。
5. 如果页面空白或数据全空，再回头确认 schema、GTFS 数据、API Key 和实时采集服务。

## 高价值验证

- `cd frontend && npm run build`: 前端改动后的最低构建校验。
- `cd backend && python3 tests/test_api_quick.py`: 适合冒烟确认 API 整体没挂。
- `cd backend && python3 tests/test_punctuality.py`: 准点率链路改动后的重点检查。
- `backend/tests/check_db.py`、`backend/tests/check_data_detail.py`: 适合怀疑 schema 或导入数据异常时使用。

## 常见根因映射

- `health` 失败: 数据库、schema 或连接配置问题。
- 后端正常但准点率全空: 实时数据、采集服务、准点率表或配置问题。
- 前端能打开但一直跳登录: token、401 处理或路由守卫问题。
- 页面接口报错: Axios 路径、`region` 透传、权限接口或后端返回结构变化。
- 端口占用或假存活: `/tmp` PID 残留或旧进程未退出。

## 输出要求

- 不只说命令失败，要说失败落在哪一层。
- 能给出下一步最短验证动作时，优先给具体动作，不给泛泛建议。
