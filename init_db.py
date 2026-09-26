# -*- coding: utf-8 -*-
"""Создаёт базу данных и заполняет её тестовыми данными.
Запуск: python init_db.py
"""
from datetime import date, timedelta

from app import create_app
from models import db, User, Category, Manufacturer, Supplier, Product, Order


def run():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ---- Пользователи ----
        users = [
            User(login="client", full_name="Иванов Иван Иванович", role="client"),
            User(login="manager", full_name="Петрова Мария Сергеевна", role="manager"),
            User(login="admin", full_name="Сидоров Алексей Викторович", role="admin"),
        ]
        passwords = {"client": "client123", "manager": "manager123", "admin": "admin123"}
        for u in users:
            u.set_password(passwords[u.login])
        db.session.add_all(users)

        # ---- Справочники ----
        categories = {name: Category(name=name) for name in ["Видеокарты", "Процессоры", "ОЗУ"]}
        db.session.add_all(categories.values())

        manufacturers = {
            name: Manufacturer(name=name)
            for name in ["NVIDIA (ASUS)", "NVIDIA (MSI)", "AMD", "Intel", "Kingston", "Corsair", "G.Skill"]
        }
        db.session.add_all(manufacturers.values())

        suppliers = {
            name: Supplier(name=name)
            for name in ["ООО \u00abТехноПоставка\u00bb", "ИП Смирнов", "ООО \u00abКомпьютерный Мир\u00bb"]
        }
        db.session.add_all(suppliers.values())
        db.session.flush()

        # ---- Товары ----
        products = [
            Product(
                name="Видеокарта ASUS GeForce RTX 4070 12GB",
                category=categories["Видеокарты"],
                description="Игровая видеокарта на чипе NVIDIA RTX 4070, 12 ГБ GDDR6X",
                manufacturer=manufacturers["NVIDIA (ASUS)"],
                supplier=suppliers["ООО \u00abТехноПоставка\u00bb"],
                price=64990,
                unit="шт.",
                quantity=8,
                discount=20,
            ),
            Product(
                name="Видеокарта MSI GeForce RTX 4060 Ti 8GB",
                category=categories["Видеокарты"],
                description="Видеокарта среднего класса, 8 ГБ GDDR6, для игр в 1440p",
                manufacturer=manufacturers["NVIDIA (MSI)"],
                supplier=suppliers["ИП Смирнов"],
                price=42990,
                unit="шт.",
                quantity=0,
                discount=0,
            ),
            Product(
                name="Видеокарта AMD Radeon RX 7800 XT 16GB",
                category=categories["Видеокарты"],
                description="Видеокарта AMD с 16 ГБ памяти для требовательных игр",
                manufacturer=manufacturers["AMD"],
                supplier=suppliers["ООО \u00abКомпьютерный Мир\u00bb"],
                price=54990,
                unit="шт.",
                quantity=5,
                discount=5,
            ),
            Product(
                name="Процессор Intel Core i5-13400F",
                category=categories["Процессоры"],
                description="10 ядер, 16 потоков, сокет LGA1700, без встроенной графики",
                manufacturer=manufacturers["Intel"],
                supplier=suppliers["ООО \u00abТехноПоставка\u00bb"],
                price=18990,
                unit="шт.",
                quantity=15,
                discount=0,
            ),
            Product(
                name="Процессор AMD Ryzen 5 7600X",
                category=categories["Процессоры"],
                description="6 ядер, 12 потоков, сокет AM5, встроенная графика Radeon",
                manufacturer=manufacturers["AMD"],
                supplier=suppliers["ИП Смирнов"],
                price=21990,
                unit="шт.",
                quantity=3,
                discount=18,
            ),
            Product(
                name="Процессор Intel Core i9-14900K",
                category=categories["Процессоры"],
                description="Флагманский процессор, 24 ядра, сокет LGA1700",
                manufacturer=manufacturers["Intel"],
                supplier=suppliers["ООО \u00abКомпьютерный Мир\u00bb"],
                price=54990,
                unit="шт.",
                quantity=0,
                discount=0,
            ),
            Product(
                name="ОЗУ Kingston FURY Beast 16GB DDR4 3200MHz",
                category=categories["ОЗУ"],
                description="Комплект 2х8 ГБ, частота 3200 МГц, radiator для охлаждения",
                manufacturer=manufacturers["Kingston"],
                supplier=suppliers["ООО \u00abТехноПоставка\u00bb"],
                price=4290,
                unit="комплект",
                quantity=40,
                discount=0,
            ),
            Product(
                name="ОЗУ Corsair Vengeance 32GB DDR5 6000MHz",
                category=categories["ОЗУ"],
                description="Комплект 2х16 ГБ, высокая частота для новых платформ",
                manufacturer=manufacturers["Corsair"],
                supplier=suppliers["ИП Смирнов"],
                price=11990,
                unit="комплект",
                quantity=6,
                discount=25,
            ),
            Product(
                name="ОЗУ G.Skill Trident Z5 32GB DDR5 6400MHz",
                category=categories["ОЗУ"],
                description="Игровая память с RGB-подсветкой, комплект 2х16 ГБ",
                manufacturer=manufacturers["G.Skill"],
                supplier=suppliers["ООО \u00abКомпьютерный Мир\u00bb"],
                price=13490,
                unit="комплект",
                quantity=12,
                discount=0,
            ),
        ]
        db.session.add_all(products)
        db.session.flush()

        # ---- Заказы ----
        orders = [
            Order(
                article="ORD-0001",
                product=products[0],
                quantity=1,
                status="Новый",
                pickup_address="г. Москва, ул. Ленина, д. 5, пункт выдачи №1",
                order_date=date.today() - timedelta(days=2),
                issue_date=None,
            ),
            Order(
                article="ORD-0002",
                product=products[3],
                quantity=2,
                status="Выдан",
                pickup_address="г. Москва, пр-т Мира, д. 12, пункт выдачи №3",
                order_date=date.today() - timedelta(days=10),
                issue_date=date.today() - timedelta(days=6),
            ),
            Order(
                article="ORD-0003",
                product=products[6],
                quantity=3,
                status="В обработке",
                pickup_address="г. Санкт-Петербург, Невский пр-т, д. 20",
                order_date=date.today() - timedelta(days=1),
                issue_date=None,
            ),
        ]
        db.session.add_all(orders)

        db.session.commit()
        print("База данных успешно создана и заполнена тестовыми данными.")
        print("Логины для входа:")
        for login, pwd in passwords.items():
            print(f"  {login} / {pwd}")


if __name__ == "__main__":
    run()
