from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
import os
import json
import uuid
import logging

# Создание приложения Flask
app = Flask(__name__)

# Конфигурация приложения
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecoslastin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Создаем папку для загрузок если её нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Инициализация расширений
db = SQLAlchemy(app)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()]
)

# Константы
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# =============================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================

def allowed_file(filename):
    """Проверка допустимости файла"""
    return ('.' in filename and 
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS and 
            not filename.startswith('.') and
            len(filename) < 100)

def generate_filename(original_filename, file_type):
    """Генерация уникального имени файла"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    extension = original_filename.rsplit('.', 1)[1].lower()
    return f"{file_type}_{timestamp}_{unique_id}.{extension}"

# =============================
# МОДЕЛИ БАЗЫ ДАННЫХ
# =============================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PriceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50))
    message = db.Column(db.Text)
    response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='new')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    image_url = db.Column(db.String(300))
    category = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(300))
    card_type = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    image_url = db.Column(db.String(300))
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# =============================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# =============================

def init_db():
    """Инициализация базы данных"""
    with app.app_context():
        try:
            # Создаем таблицы
            db.create_all()
            
            # Создаём админа по умолчанию, если его нет
            if not User.query.filter_by(username='admin').first():
                admin_user = User(
                    username='admin',
                    email='admin@ecoslastin.kg',
                    password_hash=generate_password_hash('eko2025'),
                    role='superadmin'
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Администратор создан: admin / eko2025")
            
            # Создаем начальные карточки если их нет
            if not Card.query.first():
                initial_cards = [
                    Card(
                        title="🌱 Чистый Состав",
                        description="Создан только из природных компонентов. Без искусственных подсластителей, красителей и ГМО.",
                        image_url="static/IMG_9896.DNG",
                        card_type="benefit"
                    ),
                    Card(
                        title="💫 Высокая Сладость",
                        description="Обладает сверхвысокой интенсивностью сладости. 1 кг продукта заменяет до 400 кг сахара.",
                        image_url="static/IMG_9893.DNG",
                        card_type="benefit"
                    ),
                    Card(
                        title="🔥 Термостабильность",
                        description="Идеален для приготовления горячих напитков и любой выпечки, сохраняя свойства при нагреве.",
                        image_url="static/IMG_9894.DNG",
                        card_type="benefit"
                    ),
                    Card(
                        title="🍯 Натуральный Сироп",
                        description="Натуральный сироп 'Эко-Сластин X-8' без консервантов. Прозрачный и чистый продукт для здорового питания.",
                        image_url="static/sirop.png",
                        card_type="benefit"
                    )
                ]
                db.session.bulk_save_objects(initial_cards)
                db.session.commit()
                print("✅ Начальные карточки созданы")
                
        except Exception as e:
            print(f"❌ Ошибка инициализации БД: {e}")

# =============================
# ДЕКОРАТОРЫ
# =============================

def login_required(f):
    """Декоратор для проверки авторизации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Требуется авторизация'}), 401
        user = User.query.get(session['user_id'])
        if not user or user.role not in ['admin', 'superadmin']:
            return jsonify({'success': False, 'message': 'Недостаточно прав'}), 403
        return f(*args, **kwargs)
    return decorated_function

# =============================
# ОБРАБОТЧИКИ ОШИБОК
# =============================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# =============================
# ОСНОВНЫЕ РОУТЫ
# =============================

@app.route('/')
def index():
    """Главная страница"""
    try:
        benefits_cards = Card.query.filter_by(card_type='benefit', is_active=True).order_by(Card.id).all()
        news_items = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).limit(3).all()
        return render_template('index.html', benefits_cards=benefits_cards, news_items=news_items)
    except Exception as e:
        print(f"Ошибка загрузки главной страницы: {e}")
        return render_template('index.html', benefits_cards=[], news_items=[])

@app.route('/login', methods=['GET'])
def login_page():
    """Страница входа"""
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin_page():
    """Админ-панель"""
    return render_template('admin.html')

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    return redirect(url_for('login_page', logout='1'))

# =============================
# API: АВТОРИЗАЦИЯ
# =============================

@app.route('/login', methods=['POST'])
def login():
    """API для входа в систему"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Заполните все поля'}), 400

    try:
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return jsonify({'success': True, 'message': f'Вход выполнен. Привет, {user.username}!'})

        return jsonify({'success': False, 'message': 'Неверный логин или пароль'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500

# =============================
# API: ЗАГРУЗКА ИЗОБРАЖЕНИЙ
# =============================

@app.route('/api/upload-image', methods=['POST'])
@login_required
def upload_image():
    """API для загрузки изображений"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'Файл не найден'}), 400
        
        file = request.files['image']
        file_type = request.form.get('type', 'general')
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Файл не выбран'}), 400
        
        if file and allowed_file(file.filename):
            # Проверка размера файла
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                return jsonify({'success': False, 'message': 'Файл слишком большой'}), 400
            
            # Создаем папки если их нет
            upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], file_type)
            os.makedirs(upload_folder, exist_ok=True)
            
            # Генерируем уникальное имя файла
            filename = generate_filename(file.filename, file_type)
            file_path = os.path.join(upload_folder, filename)
            
            file.save(file_path)
            image_url = f"static/uploads/{file_type}/{filename}"
            
            return jsonify({
                'success': True, 
                'message': 'Файл успешно загружен',
                'image_url': image_url,
                'filename': filename
            })
        else:
            return jsonify({'success': False, 'message': 'Недопустимый тип файла'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка загрузки: {str(e)}'}), 500

# =============================
# API: КАРТОЧКИ
# =============================

@app.route('/api/cards', methods=['GET'])
@login_required
def get_cards():
    """API для получения карточек"""
    try:
        cards = Card.query.order_by(Card.id).all()
        return jsonify([{
            'id': c.id,
            'title': c.title,
            'description': c.description,
            'image_url': c.image_url,
            'card_type': c.card_type,
            'is_active': c.is_active,
            'created_at': c.created_at.strftime('%d.%m.%Y %H:%M')
        } for c in cards])
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/cards', methods=['POST'])
@login_required
def create_card():
    """API для создания карточки"""
    try:
        data = request.get_json() or {}
        if not data.get('title') or not data.get('description'):
            return jsonify({'success': False, 'message': 'Заполните заголовок и описание'}), 400
            
        card = Card(
            title=data.get('title', ''),
            description=data.get('description', ''),
            image_url=data.get('image_url', ''),
            card_type=data.get('card_type', 'benefit')
        )
        db.session.add(card)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Карточка создана'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/cards/<int:card_id>', methods=['PATCH'])
@login_required
def update_card(card_id):
    """API для обновления карточки"""
    try:
        card = Card.query.get_or_404(card_id)
        data = request.get_json() or {}
        
        if 'title' in data:
            card.title = data['title']
        if 'description' in data:
            card.description = data['description']
        if 'image_url' in data:
            card.image_url = data['image_url']
        if 'is_active' in data:
            card.is_active = data['is_active']
        
        card.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Карточка обновлена'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/cards/<int:card_id>', methods=['DELETE'])
@login_required
def delete_card(card_id):
    """API для удаления карточки"""
    try:
        card = Card.query.get_or_404(card_id)
        db.session.delete(card)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Карточка удалена'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================
# API: НОВОСТИ
# =============================

@app.route('/api/news', methods=['GET'])
@login_required
def get_news():
    """API для получения новостей"""
    try:
        news = News.query.order_by(News.created_at.desc()).all()
        return jsonify([{
            'id': n.id,
            'title': n.title,
            'content': n.content,
            'image_url': n.image_url,
            'is_published': n.is_published,
            'created_at': n.created_at.strftime('%d.%m.%Y %H:%M')
        } for n in news])
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/news', methods=['POST'])
@login_required
def create_news():
    """API для создания новости"""
    try:
        data = request.get_json() or {}
        if not data.get('title') or not data.get('content'):
            return jsonify({'success': False, 'message': 'Заполните заголовок и содержание'}), 400
            
        news = News(
            title=data.get('title', ''),
            content=data.get('content', ''),
            image_url=data.get('image_url', ''),
            is_published=data.get('is_published', True)
        )
        db.session.add(news)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Новость создана'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/news/<int:news_id>', methods=['PATCH'])
@login_required
def update_news(news_id):
    """API для обновления новости"""
    try:
        news = News.query.get_or_404(news_id)
        data = request.get_json() or {}
        
        if 'title' in data:
            news.title = data['title']
        if 'content' in data:
            news.content = data['content']
        if 'image_url' in data:
            news.image_url = data['image_url']
        if 'is_published' in data:
            news.is_published = data['is_published']
        
        news.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Новость обновлена'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/news/<int:news_id>', methods=['DELETE'])
@login_required
def delete_news(news_id):
    """API для удаления новости"""
    try:
        news = News.query.get_or_404(news_id)
        db.session.delete(news)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Новость удалена'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================
# API: ЗАЯВКИ
# =============================

@app.route('/api/submit-request', methods=['POST'])
def submit_request():
    """API для отправки заявки"""
    try:
        data = request.get_json() or {}
        if not data.get('name') or not data.get('email'):
            return jsonify({'success': False, 'message': 'Заполните имя и email'}), 400
            
        req = PriceRequest(
            name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            message=data.get('message', '')
        )
        db.session.add(req)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Заявка принята'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/requests', methods=['GET'])
@login_required
def get_requests():
    """API для получения заявок"""
    try:
        rows = PriceRequest.query.order_by(PriceRequest.created_at.desc()).all()
        out = [{
            'id': r.id,
            'name': r.name,
            'email': r.email,
            'phone': r.phone,
            'message': r.message,
            'response': r.response,
            'created_at': r.created_at.strftime('%d.%m.%Y %H:%M'),
            'status': r.status
        } for r in rows]
        return jsonify(out)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/requests/<int:request_id>', methods=['DELETE'])
@login_required
def delete_request(request_id):
    """API для удаления заявки"""
    try:
        r = PriceRequest.query.get_or_404(request_id)
        db.session.delete(r)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/requests/<int:request_id>', methods=['PATCH'])
@login_required
def update_request(request_id):
    """API для обновления заявки"""
    try:
        data = request.get_json() or {}
        r = PriceRequest.query.get_or_404(request_id)
        if 'response' in data:
            r.response = data['response']
        if 'status' in data:
            r.status = data['status']
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================
# API: СТАТИСТИКА
# =============================

@app.route('/api/dashboard-stats', methods=['GET'])
@login_required
def dashboard_stats():
    """API для получения статистики"""
    try:
        total_requests = PriceRequest.query.count()
        new_requests = PriceRequest.query.filter_by(status='new').count()
        total_users = User.query.count()
        total_cards = Card.query.count()
        total_news = News.query.count()
        recent = PriceRequest.query.order_by(PriceRequest.created_at.desc()).limit(5).all()
        recent_data = [{'id': r.id, 'name': r.name, 'created_at': r.created_at.strftime('%d.%m.%Y')} for r in recent]
        return jsonify({
            'total_requests': total_requests,
            'new_requests': new_requests,
            'total_users': total_users,
            'total_cards': total_cards,
            'total_news': total_news,
            'recent_requests': recent_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================
# API: ПОЛЬЗОВАТЕЛИ
# =============================

@app.route('/api/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """API для получения пользователей"""
    try:
        users = User.query.all()
        return jsonify([{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'created_at': u.created_at.strftime('%d.%m.%Y')
        } for u in users])
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    """API для создания пользователя"""
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'admin')

        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'Заполните username, email и password'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Пользователь с таким именем уже существует'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Пользователь с таким email уже существует'}), 400

        user = User(username=username, email=email, password_hash=generate_password_hash(password), role=role)
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Пользователь создан'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """API для удаления пользователя"""
    try:
        if user_id == session.get('user_id'):
            return jsonify({'success': False, 'message': 'Нельзя удалить самого себя'}), 400
            
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PATCH'])
@login_required
@admin_required
def update_user(user_id):
    """API для обновления пользователя"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json() or {}

        if 'role' in data:
            user.role = data['role']
        if 'password' in data and data['password'].strip():
            user.password_hash = generate_password_hash(data['password'])

        db.session.commit()
        return jsonify({'success': True, 'message': 'Пользователь обновлён'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================
# ЗАПУСК ПРИЛОЖЕНИЯ
# =============================

if __name__ == '__main__':
    # Инициализация базы данных
    init_db()
    
    # Запуск приложения
    print("🚀 Запуск приложения ЭКО-СЛАСТИН...")
    print("📧 Админ: admin / eko2025")
    
    # Простой запуск без дополнительных зависимостей
    app.run(debug=True, host='0.0.0.0', port=5000)