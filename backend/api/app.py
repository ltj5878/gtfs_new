#!/usr/bin/env python3
"""
GTFS 数据 RESTful API 服务 — 应用入口
"""

from flask import Flask, jsonify
from flask_cors import CORS
from core.db import Database
from core.schema_bootstrap import ensure_feature_schemas
import os
import sys

# 将 backend 目录加入 sys.path，确保各模块可被导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.models import init_default_user
from api.helpers import error_response

# 导入所有 Blueprint
from auth.routes import auth_bp
from api.gtfs import gtfs_bp
from api.realtime import realtime_bp
from api.punctuality import punctuality_bp
from api.user_features import user_features_bp
from api.admin import admin_bp
from api.health_alerts import health_alerts_bp
from api.analysis import analysis_bp
from api.carbon import carbon_bp

app = Flask(__name__)
CORS(app)

# 注册所有 Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(gtfs_bp)
app.register_blueprint(realtime_bp)
app.register_blueprint(punctuality_bp)
app.register_blueprint(user_features_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(health_alerts_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(carbon_bp)


@app.before_request
def before_first_request():
    """初始化数据库连接池"""
    if Database._connection_pool is None:
        Database.initialize()
        init_default_user()
        ensure_feature_schemas()


@app.teardown_appcontext
def shutdown_session(exception=None):
    """请求结束时的清理工作"""
    pass


@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify(error_response("接口不存在", 404)), 404


@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    return jsonify(error_response("服务器内部错误", 500)), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'

    print(f"启动 GTFS API 服务...")
    print(f"端口: {port}")
    print(f"调试模式: {debug}")
    print(f"API 文档: http://localhost:{port}/api/health")

    app.run(host='0.0.0.0', port=port, debug=debug)
