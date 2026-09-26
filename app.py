# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
)
from werkzeug.utils import secure_filename
from PIL import Image

from models import db, User, Category, Manufacturer, Supplier, Product, Order, ORDER_STATUSES

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
MAX_IMAGE_SIZE = (300, 200)
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif"}


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "pc-shop-demo-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "shop.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    db.init_app(app)
    register_routes(app)
    return app


# ---------------------------------------------------------------------------
# Вспомогательные функции доступа
# ---------------------------------------------------------------------------

def current_role():
    return session.get("role", "guest")


def current_user_name():
    return session.get("full_name", "Гость")


def login_required_roles(*roles):
    """Разрешить доступ только перечисленным ролям (гость = 'guest')."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if current_role() not in roles:
                flash("У вас нет доступа к этому разделу.", "error")
                return redirect(url_for("products_page"))
            return wrapped_view_call(view, *args, **kwargs)
        return wrapped
    return decorator


def wrapped_view_call(view, *args, **kwargs):
    return view(*args, **kwargs)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def save_product_image(file_storage, old_path=None):
    """Сохраняет изображение товара, сжимая его до 300x200, удаляет старое."""
    if not file_storage or file_storage.filename == "":
        return old_path
    if not allowed_file(file_storage.filename):
        flash("Недопустимый формат изображения. Разрешены: png, jpg, jpeg, gif.", "error")
        return old_path

    filename = secure_filename(file_storage.filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    filename = f"{timestamp}_{filename}"
    full_path = os.path.join(UPLOAD_FOLDER, filename)

    image = Image.open(file_storage)
    image = image.convert("RGB")
    image.thumbnail(MAX_IMAGE_SIZE)
    image.save(full_path, quality=90)

    if old_path and old_path.startswith("uploads/"):
        old_full = os.path.join(BASE_DIR, "static", old_path)
        if os.path.exists(old_full):
            os.remove(old_full)

    return f"uploads/{filename}"


def register_routes(app):

    # ------------------------------------------------------------------
    # Авторизация
    # ------------------------------------------------------------------
    @app.route("/", methods=["GET"])
    def index():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            login_value = request.form.get("login", "").strip()
            password = request.form.get("password", "")
            user = User.query.filter_by(login=login_value).first()
            if user and user.check_password(password):
                session["user_id"] = user.id
                session["role"] = user.role
                session["full_name"] = user.full_name
                return redirect(url_for("products_page"))
            flash("Неверный логин или пароль.", "error")
        return render_template("login.html")

    @app.route("/guest")
    def guest_login():
        session.clear()
        session["role"] = "guest"
        session["full_name"] = "Гость"
        return redirect(url_for("products_page"))

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ------------------------------------------------------------------
    # Товары
    # ------------------------------------------------------------------
    @app.route("/products")
    def products_page():
        if "role" not in session:
            return redirect(url_for("login"))
        role = current_role()
        can_manage = role == "admin"
        can_filter = role in ("manager", "admin")

        products = Product.query.order_by(Product.id).all()
        suppliers = Supplier.query.order_by(Supplier.name).all()
        return render_template(
            "products.html",
            products=products,
            products_json=json.dumps([p.to_dict() for p in products]),
            suppliers=suppliers,
            role=role,
            can_manage=can_manage,
            can_filter=can_filter,
            full_name=current_user_name(),
        )

    @app.route("/api/products")
    def api_products():
        """Реальное время: поиск + фильтр по поставщику + сортировка по количеству.
        Доступно только менеджеру и администратору."""
        if current_role() not in ("manager", "admin"):
            abort(403)

        query = Product.query
        search = request.args.get("q", "").strip()
        supplier_id = request.args.get("supplier", "")
        sort = request.args.get("sort", "")  # 'asc' | 'desc' | ''

        if search:
            like = f"%{search}%"
            query = query.join(Category).join(Manufacturer).join(Supplier).filter(
                db.or_(
                    Product.name.ilike(like),
                    Product.description.ilike(like),
                    Category.name.ilike(like),
                    Manufacturer.name.ilike(like),
                    Supplier.name.ilike(like),
                    Product.unit.ilike(like),
                )
            )
        if supplier_id:
            query = query.filter(Product.supplier_id == int(supplier_id))

        if sort == "asc":
            query = query.order_by(Product.quantity.asc())
        elif sort == "desc":
            query = query.order_by(Product.quantity.desc())
        else:
            query = query.order_by(Product.id.asc())

        products = query.all()
        return jsonify([p.to_dict() for p in products])

    @app.route("/products/new", methods=["GET", "POST"])
    def product_new():
        if current_role() != "admin":
            flash("Добавлять товары может только администратор.", "error")
            return redirect(url_for("products_page"))
        categories = Category.query.order_by(Category.name).all()
        manufacturers = Manufacturer.query.order_by(Manufacturer.name).all()
        suppliers = Supplier.query.order_by(Supplier.name).all()
        next_id = (db.session.query(db.func.max(Product.id)).scalar() or 0) + 1

        if request.method == "POST":
            error = validate_product_form(request.form)
            if error:
                flash(error, "error")
            else:
                image_path = save_product_image(request.files.get("image"))
                product = Product(
                    name=request.form["name"].strip(),
                    category_id=int(request.form["category_id"]),
                    description=request.form.get("description", "").strip(),
                    manufacturer_id=int(request.form["manufacturer_id"]),
                    supplier_id=int(request.form["supplier_id"]),
                    price=float(request.form["price"]),
                    unit=request.form["unit"].strip(),
                    quantity=int(request.form["quantity"]),
                    discount=int(request.form.get("discount") or 0),
                    image_path=image_path,
                )
                db.session.add(product)
                db.session.commit()
                flash("Товар успешно добавлен.", "success")
                return redirect(url_for("products_page"))

        return render_template(
            "product_form.html", product=None, categories=categories,
            manufacturers=manufacturers, suppliers=suppliers, next_id=next_id,
        )

    @app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
    def product_edit(product_id):
        if current_role() != "admin":
            flash("Редактировать товары может только администратор.", "error")
            return redirect(url_for("products_page"))
        product = Product.query.get_or_404(product_id)
        categories = Category.query.order_by(Category.name).all()
        manufacturers = Manufacturer.query.order_by(Manufacturer.name).all()
        suppliers = Supplier.query.order_by(Supplier.name).all()

        if request.method == "POST":
            error = validate_product_form(request.form)
            if error:
                flash(error, "error")
            else:
                product.image_path = save_product_image(request.files.get("image"), product.image_path)
                product.name = request.form["name"].strip()
                product.category_id = int(request.form["category_id"])
                product.description = request.form.get("description", "").strip()
                product.manufacturer_id = int(request.form["manufacturer_id"])
                product.supplier_id = int(request.form["supplier_id"])
                product.price = float(request.form["price"])
                product.unit = request.form["unit"].strip()
                product.quantity = int(request.form["quantity"])
                product.discount = int(request.form.get("discount") or 0)
                db.session.commit()
                flash("Товар успешно обновлён.", "success")
                return redirect(url_for("products_page"))

        return render_template(
            "product_form.html", product=product, categories=categories,
            manufacturers=manufacturers, suppliers=suppliers, next_id=product.id,
        )

    @app.route("/products/<int:product_id>/delete", methods=["POST"])
    def product_delete(product_id):
        if current_role() != "admin":
            flash("Удалять товары может только администратор.", "error")
            return redirect(url_for("products_page"))
        product = Product.query.get_or_404(product_id)
        in_order = Order.query.filter_by(product_id=product.id).first()
        if in_order:
            flash(
                f'Нельзя удалить товар «{product.name}» — он присутствует в заказе {in_order.article}.',
                "error",
            )
            return redirect(url_for("products_page"))
        if product.image_path and product.image_path.startswith("uploads/"):
            full_path = os.path.join(BASE_DIR, "static", product.image_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        db.session.delete(product)
        db.session.commit()
        flash("Товар удалён.", "success")
        return redirect(url_for("products_page"))

    # ------------------------------------------------------------------
    # Заказы
    # ------------------------------------------------------------------
    @app.route("/orders")
    def orders_page():
        if current_role() not in ("manager", "admin"):
            flash("Раздел «Заказы» доступен менеджеру и администратору.", "error")
            return redirect(url_for("products_page"))
        orders = Order.query.order_by(Order.id.desc()).all()
        return render_template(
            "orders.html", orders=orders, role=current_role(),
            can_manage=current_role() == "admin", full_name=current_user_name(),
        )

    @app.route("/orders/new", methods=["GET", "POST"])
    def order_new():
        if current_role() != "admin":
            flash("Добавлять заказы может только администратор.", "error")
            return redirect(url_for("orders_page"))
        products = Product.query.order_by(Product.name).all()
        next_num = (db.session.query(db.func.max(Order.id)).scalar() or 0) + 1
        suggested_article = f"ORD-{next_num:04d}"

        if request.method == "POST":
            error = validate_order_form(request.form)
            if error:
                flash(error, "error")
            else:
                order = Order(
                    article=request.form["article"].strip(),
                    product_id=int(request.form["product_id"]),
                    quantity=int(request.form["quantity"]),
                    status=request.form["status"],
                    pickup_address=request.form["pickup_address"].strip(),
                    order_date=datetime.strptime(request.form["order_date"], "%Y-%m-%d").date(),
                    issue_date=(
                        datetime.strptime(request.form["issue_date"], "%Y-%m-%d").date()
                        if request.form.get("issue_date") else None
                    ),
                )
                db.session.add(order)
                db.session.commit()
                flash("Заказ успешно добавлен.", "success")
                return redirect(url_for("orders_page"))

        return render_template(
            "order_form.html", order=None, products=products,
            statuses=ORDER_STATUSES, suggested_article=suggested_article,
        )

    @app.route("/orders/<int:order_id>/edit", methods=["GET", "POST"])
    def order_edit(order_id):
        if current_role() != "admin":
            flash("Редактировать заказы может только администратор.", "error")
            return redirect(url_for("orders_page"))
        order = Order.query.get_or_404(order_id)
        products = Product.query.order_by(Product.name).all()

        if request.method == "POST":
            error = validate_order_form(request.form)
            if error:
                flash(error, "error")
            else:
                order.article = request.form["article"].strip()
                order.product_id = int(request.form["product_id"])
                order.quantity = int(request.form["quantity"])
                order.status = request.form["status"]
                order.pickup_address = request.form["pickup_address"].strip()
                order.order_date = datetime.strptime(request.form["order_date"], "%Y-%m-%d").date()
                order.issue_date = (
                    datetime.strptime(request.form["issue_date"], "%Y-%m-%d").date()
                    if request.form.get("issue_date") else None
                )
                db.session.commit()
                flash("Заказ успешно обновлён.", "success")
                return redirect(url_for("orders_page"))

        return render_template(
            "order_form.html", order=order, products=products,
            statuses=ORDER_STATUSES, suggested_article=order.article,
        )

    @app.route("/orders/<int:order_id>/delete", methods=["POST"])
    def order_delete(order_id):
        if current_role() != "admin":
            flash("Удалять заказы может только администратор.", "error")
            return redirect(url_for("orders_page"))
        order = Order.query.get_or_404(order_id)
        db.session.delete(order)
        db.session.commit()
        flash("Заказ удалён.", "success")
        return redirect(url_for("orders_page"))


def validate_product_form(form):
    try:
        price = float(form.get("price", ""))
        if price < 0:
            return "Цена не может быть отрицательной."
    except (TypeError, ValueError):
        return "Укажите корректную цену."
    try:
        quantity = int(form.get("quantity", ""))
        if quantity < 0:
            return "Количество на складе не может быть отрицательным."
    except (TypeError, ValueError):
        return "Укажите корректное количество."
    discount = form.get("discount") or "0"
    try:
        discount_val = int(discount)
        if not (0 <= discount_val <= 100):
            return "Скидка должна быть от 0 до 100%."
    except ValueError:
        return "Укажите корректную скидку."
    if not form.get("name", "").strip():
        return "Укажите наименование товара."
    return None


def validate_order_form(form):
    if not form.get("article", "").strip():
        return "Укажите артикул заказа."
    if not form.get("pickup_address", "").strip():
        return "Укажите адрес пункта выдачи."
    if not form.get("order_date"):
        return "Укажите дату заказа."
    try:
        int(form.get("quantity", ""))
    except ValueError:
        return "Укажите корректное количество."
    return None


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
