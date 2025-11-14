from models import db, User, PriceRequest, Product
from config import Config
import hashlib

def init_db(app):
    """Инициализация базы данных"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        create_default_admin()

def create_default_admin():
    """Создание администратора по умолчанию"""
    admin_exists = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
    if not admin_exists:
        # Простой хэш пароля (в продакшене используйте bcrypt)
        password_hash = hashlib.sha256(Config.ADMIN_PASSWORD.encode()).hexdigest()
        
        admin_user = User(
            username=Config.ADMIN_USERNAME,
            email=Config.ADMIN_EMAIL,
            password_hash=password_hash,
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Создан администратор по умолчанию")

def add_sample_data():
    """Добавление тестовых данных"""
    # Тестовые заявки
    if PriceRequest.query.count() == 0:
        sample_requests = [
            PriceRequest(
                name='ООО "Кондитер"',
                email='konditer@corp.ru',
                phone='+7 (999) 123-45-67',
                message='Объем от 500 кг.',
                status='new'
            ),
            PriceRequest(
                name='ИП Иванова А.В.',
                email='ivanova@mail.ru',
                phone='+996 (555) 987-65-43',
                message='Для частного производства.',
                status='viewed'
            )
        ]
        for request in sample_requests:
            db.session.add(request)
        
        # Тестовые продукты
        sample_products = [
            Product(
                name='ЭКО-СЛАСТИН Премиум',
                description='Натуральный подсластитель высшего качества. 1 кг заменяет до 400 кг сахара.',
                image_url='product1.jpg',
                price=1500.00,
                is_active=True
            )
        ]
        for product in sample_products:
            db.session.add(product)
        
        db.session.commit()