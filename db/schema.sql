-- ============================================================
-- Скрипт создания базы данных "Магазин комплектующих ПК"
-- Соответствует 3 нормальной форме, ссылочная целостность обеспечена
-- внешними ключами. СУБД: SQLite (совместимо с адаптацией под
-- PostgreSQL/MySQL при необходимости).
-- ============================================================

DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS manufacturers;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

-- Пользователи системы (клиент, менеджер, администратор)
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    login         VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(150) NOT NULL,
    role          VARCHAR(20)  NOT NULL CHECK (role IN ('client', 'manager', 'admin'))
);

-- Категории товаров
CREATE TABLE categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Производители
CREATE TABLE manufacturers (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Поставщики
CREATE TABLE suppliers (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(150) NOT NULL UNIQUE
);

-- Товары (комплектующие ПК)
CREATE TABLE products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(150)   NOT NULL,
    category_id     INTEGER        NOT NULL,
    description     TEXT,
    manufacturer_id INTEGER        NOT NULL,
    supplier_id     INTEGER        NOT NULL,
    price           NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    unit            VARCHAR(20)    NOT NULL DEFAULT 'шт.',
    quantity        INTEGER        NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    discount        INTEGER        NOT NULL DEFAULT 0 CHECK (discount BETWEEN 0 AND 100),
    image_path      VARCHAR(255),
    FOREIGN KEY (category_id)     REFERENCES categories(id),
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturers(id),
    FOREIGN KEY (supplier_id)     REFERENCES suppliers(id)
);

-- Заказы
CREATE TABLE orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    article        VARCHAR(50)  NOT NULL UNIQUE,
    product_id     INTEGER      NOT NULL,
    quantity       INTEGER      NOT NULL DEFAULT 1 CHECK (quantity > 0),
    status         VARCHAR(30)  NOT NULL DEFAULT 'Новый',
    pickup_address VARCHAR(255) NOT NULL,
    order_date     DATE         NOT NULL,
    issue_date     DATE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX idx_products_category     ON products(category_id);
CREATE INDEX idx_products_manufacturer ON products(manufacturer_id);
CREATE INDEX idx_products_supplier     ON products(supplier_id);
CREATE INDEX idx_orders_product        ON orders(product_id);
