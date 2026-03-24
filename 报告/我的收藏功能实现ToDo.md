# 我的收藏 (My Favorites) 功能实现 ToDo 列表 (数据库存储版)

## 1. 核心目标
实现一个持久化的“我的收藏”系统，允许用户收藏**线路**、**站点**和**准点率预测页**。数据将存储在 PostgreSQL 数据库中，并通过 Flask 后端接口进行同步，确保用户在不同设备登录后均可访问。

---

## 2. 数据库设计 (Database Layer)
在 `backend/database/` 下创建 `favorites_schema.sql` 或直接更新现有架构：
```sql
CREATE TABLE IF NOT EXISTS user_favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    region TEXT NOT NULL,
    item_type TEXT NOT NULL, -- 'route', 'stop', 'punctuality'
    item_id TEXT NOT NULL,   -- route_id 或 stop_id
    item_name TEXT,          -- 冗余存储名称，减少连表查询
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, region, item_type, item_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (region) REFERENCES regions(region_id)
);

CREATE INDEX idx_user_favorites_user ON user_favorites(user_id);
```

---

## 3. 后端接口实现 (Backend Layer)
在 `backend/api/app.py` 中新增收藏相关接口，并集成 JWT 认证。

- [ ] **接口设计**：
  - `GET /api/favorites`：获取当前登录用户的所有收藏。
  - `POST /api/favorites`：添加收藏（需校验 region, item_type, item_id）。
  - `DELETE /api/favorites/<id>` 或 `DELETE /api/favorites?region=...&type=...&id=...`：取消收藏。
- [ ] **权限控制**：
  - 必须携带 `Authorization: Bearer <token>` 请求头。
  - 后端解析 token 获取 `user_id`。

---

## 4. 前端状态管理 (Store Layer)
在 `frontend/src/stores/favoriteStore.js` 中管理收藏状态。

- [ ] **Store 实现**：
  - `fetchFavorites()`：从后端拉取完整收藏列表。
  - `toggleFavorite(item)`：根据当前状态调用 POST 或 DELETE 接口。
  - `isFavorite(region, type, id)`：从本地缓存的状态中快速判断。
- [ ] **自动同步**：
  - 用户登录成功后，自动触发 `fetchFavorites()`。
  - 退出登录时，清空 Store 状态。

---

## 5. 各页面交互集成 (UI Layer)
- [ ] **线路与站点页 (`Routes.vue`, `Stops.vue`, `Detail.vue`)**：
  - 在列表项或详情页标题旁增加 `Star` 按钮。
  - 未登录用户点击收藏时，提示并引导跳转至登录页。
- [ ] **准点率分析页 (`RoutePunctuality.vue`, `StopPunctuality.vue`)**：
  - 增加“收藏此视图”按钮，支持一键保存特定线路/站点的分析页面。

---

## 6. 管理中心与入口 (Management Layer)
- [ ] **首页功能入口 (`Home.vue`)**：
  - 在“基础功能”卡片下新增“我的收藏”入口。
- [ ] **创建收藏管理页 (`Favorites.vue`)**：
  - 使用 `el-tabs` 分类展示线路、站点和分析视图。
  - **跳转逻辑**：点击收藏项时，需先调用 `regionStore.setRegion(item.region)`，再进行 `router.push`。

---

## 7. 关键逻辑点
- **数据一致性**：确保后端删除操作成功后再更新前端 Store 状态，或者使用乐观更新（Optimistic UI）。
- **性能优化**：在获取线路/站点列表时，后端可考虑通过 `LEFT JOIN` 一次性返回当前用户的收藏状态，减少前端循环判断的压力。

---

## 8. 验收标准
1. [ ] **跨设备同步**：在设备 A 收藏某线路，设备 B 登录相同账号后能立即看到该收藏。
2. [ ] **权限隔离**：用户 A 无法看到用户 B 的收藏。
3. [ ] **异常处理**：Token 过期时，收藏操作应能优雅提示“请先登录”。
4. [ ] **地区自动切换**：点击跨地区的收藏项，系统能平滑切换 region 并加载数据。
