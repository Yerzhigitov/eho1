from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, PriceRequest, Product
from config import Config
import hashlib
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# Простая аутентификация (без Flask-Login для простоты)
def authenticate_user(username, password):
    """Аутентификация пользователя"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = User.query.filter_by(
        username=username, 
        password_hash=password_hash,
        is_active=True
    ).first()
    return user

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Страница входа в админ-панель"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = authenticate_user(username, password)
        if user and user.is_admin:
            session['admin_logged_in'] = True
            session['admin_user_id'] = user.id
            session.permanent = True
            
            return jsonify({'success': True, 'redirect': '/admin/'})
        else:
            return jsonify({'success': False, 'error': 'Неверные учетные данные'})
    
    return render_template('login.html')

@admin_bp.route('/admin/')
def admin_dashboard():
    """Главная страница админ-панели"""
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    
    return render_template('admin.html')

@admin_bp.route('/admin/logout')
def admin_logout():
    """Выход из админ-панели"""
    session.pop('admin_logged_in', None)
    session.pop('admin_user_id', None)
    return redirect('/admin/login')

# API endpoints для админ-панели
@admin_bp.route('/api/admin/requests')
def get_requests():
    """Получение списка заявок"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status', 'all')
        
        query = PriceRequest.query
        
        if status_filter != 'all':
            query = query.filter_by(status=status_filter)
        
        requests = query.order_by(PriceRequest.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'requests': [req.to_dict() for req in requests.items],
            'total': requests.total,
            'pages': requests.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': 'Ошибка получения данных'}), 500

@admin_bp.route('/api/admin/requests/<int:request_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_request(request_id):
    """Управление конкретной заявкой"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        price_request = PriceRequest.query.get_or_404(request_id)
        
        if request.method == 'GET':
            return jsonify(price_request.to_dict())
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'status' in data:
                price_request.status = data['status']
                price_request.updated_at = datetime.utcnow()
            
            db.session.commit()
            return jsonify({'success': True, 'request': price_request.to_dict()})
            
        elif request.method == 'DELETE':
            db.session.delete(price_request)
            db.session.commit()
            return jsonify({'success': True})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка обработки запроса'}), 500

@admin_bp.route('/api/admin/dashboard-stats')
def dashboard_stats():
    """Статистика для дашборда"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Общая статистика
        total_requests = PriceRequest.query.count()
        new_requests = PriceRequest.query.filter_by(status='new').count()
        viewed_requests = PriceRequest.query.filter_by(status='viewed').count()
        
        # Последние 5 заявок
        recent_requests = PriceRequest.query.order_by(
            PriceRequest.created_at.desc()
        ).limit(5).all()
        
        return jsonify({
            'stats': {
                'total_requests': total_requests,
                'new_requests': new_requests,
                'viewed_requests': viewed_requests
            },
            'recent_requests': [req.to_dict() for req in recent_requests]
        })
        
    except Exception as e:
        return jsonify({'error': 'Ошибка получения статистики'}), 500