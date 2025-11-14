from flask import Blueprint, request, jsonify, render_template
from models import db, PriceRequest
from datetime import datetime
import re

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('eko.html')

@main_bp.route('/api/submit-request', methods=['POST'])
def submit_request():
    """Обработка заявки с сайта"""
    try:
        data = request.get_json()
        
        # Валидация данных
        if not data.get('name') or not data.get('email'):
            return jsonify({'success': False, 'error': 'Имя и email обязательны'}), 400
        
        # Проверка email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return jsonify({'success': False, 'error': 'Некорректный email'}), 400
        
        # Создание заявки
        new_request = PriceRequest(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone', ''),
            message=data.get('message', ''),
            status='new'
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Заявка успешно отправлена!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Ошибка сервера'}), 500

@main_bp.route('/api/requests/count')
def get_requests_count():
    """Получение количества новых заявок (для дашборда)"""
    try:
        new_count = PriceRequest.query.filter_by(status='new').count()
        total_count = PriceRequest.query.count()
        
        return jsonify({
            'new_requests': new_count,
            'total_requests': total_count
        })
    except Exception as e:
        return jsonify({'error': 'Ошибка получения данных'}), 500