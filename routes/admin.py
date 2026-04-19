from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
import psutil
from database import Item, Reports, User
from functools import wraps
from flask import abort
from flask_login import current_user
admin_routes = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(func):
    """Decorator to restrict access to admin users only"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)  # Forbidden
        return func(*args, **kwargs)

    return wrapper

@admin_routes.route("/")
@admin_routes.route("/dashboard")
@login_required
@admin_required
def dashboard():
    return render_template("admin.html")


@admin_routes.route("/users")
@login_required
@admin_required
def users():
    return render_template("admin.html")


@admin_routes.route("/posts")
@login_required
@admin_required
def posts():
    return render_template("admin.html")


@admin_routes.route("/metrics")
@login_required
@admin_required
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


@admin_routes.route("/api/users")
@login_required
@admin_required
def api_users():
    """Get all users data"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Apply filters
    query = User.query
    role = request.args.get('role')
    search = request.args.get('search', '')
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.name.ilike(f'%{search}%'))
        )
    
    if role and role != 'all':
        query = query.filter(User.role == role)
    
    # Get paginated results
    users_paginated = query.paginate(page=page, per_page=per_page)
    
    users_data = []
    for user in users_paginated.items:
        post_count = Item.query.filter_by(uploader_id=user.id).count()
        users_data.append({
            'id': user.id,
            'username': user.username,
            'name': user.name or user.username,
            'email': user.email or 'N/A',
            'role': user.role,
            'posts': post_count,
            'joined': user.created_at.strftime('%Y-%m-%d'),
            '2fa': '✓' if user._2fa_enabled else '✗'
        })
    
    return jsonify({
        'users': users_data,
        'total': users_paginated.total,
        'pages': users_paginated.pages,
        'current_page': page
    })


@admin_routes.route("/api/posts")
@login_required
@admin_required
def api_posts():
    """Get all posts data"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Apply filters
    query = Item.query
    status = request.args.get('status')
    category = request.args.get('category')
    search = request.args.get('search', '')
    
    if search:
        query = query.filter(
            (Item.name.ilike(f'%{search}%')) |
            (Item.description_hu.ilike(f'%{search}%')) |
            (Item.description_en.ilike(f'%{search}%'))
        )
    
    if status and status != 'all':
        if status == 'active':
            query = query.filter(Item.active == True, Item.is_closed == False)
        elif status == 'closed':
            query = query.filter(Item.is_closed == True)
        elif status == 'inactive':
            query = query.filter(Item.active == False)
    
    if category and category != 'all':
        query = query.filter(Item.category_id == category)
    
    # Get paginated results
    posts_paginated = query.paginate(page=page, per_page=per_page)
    
    posts_data = []
    for post in posts_paginated.items:
        reporter_count = Reports.query.filter_by(item_id=post.id, pending=True).count()
        uploader = User.query.get(post.uploader_id)
        
        posts_data.append({
            'id': post.id,
            'name': post.name,
            'uploader': uploader.username if uploader else 'Unknown',
            'type': post.type.capitalize(),
            'status': 'Closed' if post.is_closed else ('Active' if post.active else 'Inactive'),
            'category': post.category.name if post.category else 'N/A',
            'reports': reporter_count,
            'posted': post.created_at.strftime('%Y-%m-%d'),
            'has_reports': reporter_count > 0
        })
    
    return jsonify({
        'posts': posts_data,
        'total': posts_paginated.total,
        'pages': posts_paginated.pages,
        'current_page': page
    })


@admin_routes.route("/api/reports")
@login_required
@admin_required
def api_reports():
    """Get all reports data"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Apply filters
    query = Reports.query
    status = request.args.get('status')
    search = request.args.get('search', '')
    
    if search:
        query = query.join(User).outerjoin(Item).filter(
            (User.username.ilike(f'%{search}%')) |
            (Item.name.ilike(f'%{search}%')) |
            (Reports.reason.ilike(f'%{search}%'))
        )
    
    if status and status != 'all':
        if status == 'pending':
            query = query.filter(Reports.pending == True)
        elif status == 'resolved':
            query = query.filter(Reports.pending == False)
    
    # Get paginated results
    reports_paginated = query.paginate(page=page, per_page=per_page)
    
    reports_data = []
    for report in reports_paginated.items:
        reporter = User.query.get(report.reporter_id)
        
        # Determine report type (item or user)
        if report.item_id:
            item = Item.query.get(report.item_id)
            target_name = item.name if item else 'Deleted Item'
            report_type = 'Item Report'
        elif report.user_id:
            reported_user = User.query.get(report.user_id)
            target_name = reported_user.username if reported_user else 'Deleted User'
            report_type = 'User Report'
        else:
            target_name = 'Unknown'
            report_type = 'Report'
        
        reports_data.append({
            'id': report.id,
            'reporter': reporter.username if reporter else 'Unknown',
            'post': target_name,
            'reason': report.reason or 'No reason',
            'status': 'Pending' if report.pending else 'Resolved',
            'created': report.created_at.strftime('%Y-%m-%d %H:%M'),
            'type': report_type
        })
    
    return jsonify({
        'reports': reports_data,
        'total': reports_paginated.total,
        'pages': reports_paginated.pages,
        'current_page': page
    })
