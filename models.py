from datetime import date
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """Пользователи системы: клиент, менеджер, администратор.
    Роль 'гость' не хранится в БД — гость не авторизован."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # client / manager / admin

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class Category(db.Model):
    """Категория товара (Видеокарты, Процессоры, ОЗУ)."""
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    products = db.relationship("Product", back_populates="category")


class Manufacturer(db.Model):
    """Производитель товара (NVIDIA, AMD, Intel, Kingston и т.д.)."""
    __tablename__ = "manufacturers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    products = db.relationship("Product", back_populates="manufacturer")


class Supplier(db.Model):
    """Поставщик товара."""
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)

    products = db.relationship("Product", back_populates="supplier")


class Product(db.Model):
    """Комплектующая ПК (видеокарта, процессор, модуль ОЗУ и т.д.)."""
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    description = db.Column(db.Text, nullable=True)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey("manufacturers.id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(20), nullable=False, default="шт.")
    quantity = db.Column(db.Integer, nullable=False, default=0)
    discount = db.Column(db.Integer, nullable=False, default=0)  # процент 0-100
    image_path = db.Column(db.String(255), nullable=True)

    category = db.relationship("Category", back_populates="products")
    manufacturer = db.relationship("Manufacturer", back_populates="products")
    supplier = db.relationship("Supplier", back_populates="products")

    @property
    def final_price(self):
        if self.discount and self.discount > 0:
            return round(float(self.price) * (1 - self.discount / 100), 2)
        return float(self.price)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.name if self.category else "",
            "description": self.description or "",
            "manufacturer": self.manufacturer.name if self.manufacturer else "",
            "supplier": self.supplier.name if self.supplier else "",
            "price": float(self.price),
            "final_price": self.final_price,
            "unit": self.unit,
            "quantity": self.quantity,
            "discount": self.discount,
            "image_path": self.image_path or "img/picture.png",
        }


ORDER_STATUSES = ["Новый", "В обработке", "Готов к выдаче", "Выдан", "Отменён"]


class Order(db.Model):
    """Заказ на комплектующую ПК."""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    article = db.Column(db.String(50), unique=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(30), nullable=False, default="Новый")
    pickup_address = db.Column(db.String(255), nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=date.today)
    issue_date = db.Column(db.Date, nullable=True)

    product = db.relationship("Product")
