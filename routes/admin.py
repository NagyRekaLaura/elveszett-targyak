from flask import Blueprint, jsonify, render_template
from flask_login import login_required
import psutil
from database import Item, Reports, User

admin_routes = Blueprint("admin", __name__, url_prefix="/admin")


@admin_routes.route("/")
@admin_routes.route("/dashboard")
@login_required
def dashboard():
    return render_template("admin.html")


@admin_routes.route("/users")
@login_required
def users():
    return render_template("admin.html")


@admin_routes.route("/posts")
@login_required
def posts():
    return render_template("admin.html")


@admin_routes.route("/metrics")
@login_required
def metrics():
    memory = psutil.virtual_memory()
    cpu_usage_percent = psutil.cpu_percent(interval=0.2)
    cpu_freq = psutil.cpu_freq()
    logical_cores = psutil.cpu_count(logical=True) or 0
    total_users = User.query.count()
    total_posts = Item.query.count()
    pending_reports = Reports.query.filter_by(pending=True).count()

    ram_total_gb = round(memory.total / (1024 ** 3), 2)
    ram_used_gb = round(memory.used / (1024 ** 3), 2)
    ram_percent_used = round(memory.percent, 1)

    cpu_current_frequency_ghz = None
    cpu_max_frequency_ghz = None
    if cpu_freq:
        cpu_current_frequency_ghz = round(cpu_freq.current / 1000, 2)
        if cpu_freq.max and cpu_freq.max > 0:
            cpu_max_frequency_ghz = round(cpu_freq.max / 1000, 2)

    return jsonify(
        {
            "ram": {
                "total_gb": ram_total_gb,
                "used_gb": ram_used_gb,
                "percent_used": ram_percent_used,
                "percent_available": round(max(0, 100 - ram_percent_used), 1),
            },
            "cpu": {
                "usage_percent": round(cpu_usage_percent, 1),
                "percent_available": round(max(0, 100 - cpu_usage_percent), 1),
                "logical_cores": logical_cores,
                "current_frequency_ghz": cpu_current_frequency_ghz,
                "max_frequency_ghz": cpu_max_frequency_ghz,
            },
            "stats": {
                "total_users": total_users,
                "total_posts": total_posts,
                "pending_reports": pending_reports,
            },
        }
    )
