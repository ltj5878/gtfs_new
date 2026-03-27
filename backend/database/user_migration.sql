-- 用户表迁移：新增角色和状态字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;

-- 将现有 admin 用户设为管理员
UPDATE users SET role = 'admin' WHERE username = 'admin';
