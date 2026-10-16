CREATE DATABASE IF NOT EXISTS inventory_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE inventory_db;

-- =========================
-- USERS
-- =========================

CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'STAFF',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- CATEGORIES
-- =========================

CREATE TABLE categories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- SUPPLIERS
-- =========================

CREATE TABLE suppliers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- PRODUCTS
-- =========================

CREATE TABLE products (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    category_id BIGINT NOT NULL,
    unit VARCHAR(30) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    import_price DECIMAL(15,2) NOT NULL DEFAULT 0,
    sale_price DECIMAL(15,2) NOT NULL DEFAULT 0,
    min_stock INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_product_category
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
);

-- =========================
-- IMPORT RECEIPTS
-- =========================

CREATE TABLE import_receipts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    supplier_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    import_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    note VARCHAR(255),

    CONSTRAINT fk_import_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(id),

    CONSTRAINT fk_import_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
);

-- =========================
-- IMPORT DETAILS
-- =========================

CREATE TABLE import_details (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    import_receipt_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,

    CONSTRAINT fk_import_detail_receipt
        FOREIGN KEY (import_receipt_id)
        REFERENCES import_receipts(id),

    CONSTRAINT fk_import_detail_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
);

-- =========================
-- EXPORT RECEIPTS
-- =========================

CREATE TABLE export_receipts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    export_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    receiver VARCHAR(150),
    note VARCHAR(255),

    CONSTRAINT fk_export_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
);

-- =========================
-- EXPORT DETAILS
-- =========================

CREATE TABLE export_details (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    export_receipt_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,

    CONSTRAINT fk_export_detail_receipt
        FOREIGN KEY (export_receipt_id)
        REFERENCES export_receipts(id),

    CONSTRAINT fk_export_detail_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
);

-- =========================
-- SAMPLE DATA
-- =========================

INSERT INTO users
(username, password, full_name, role)
VALUES
('admin', 'admin123', 'Administrator', 'ADMIN'),
('staff', 'staff123', 'Nhân viên kho', 'STAFF');

INSERT INTO categories
(name, description)
VALUES
('Điện tử', 'Các sản phẩm điện tử'),
('Văn phòng phẩm', 'Các sản phẩm văn phòng'),
('Thiết bị', 'Các thiết bị và phụ kiện');

INSERT INTO suppliers
(name, phone, email, address)
VALUES
('Nhà cung cấp ABC', '0901234567', 'abc@example.com', 'Hà Nội'),
('Nhà cung cấp XYZ', '0912345678', 'xyz@example.com', 'Hồ Chí Minh');

INSERT INTO products
(code, name, category_id, unit, quantity, import_price, sale_price, min_stock)
VALUES
('SP001', 'Laptop Dell', 1, 'Cái', 50, 15000000, 18000000, 10),
('SP002', 'Chuột Logitech', 1, 'Cái', 100, 250000, 350000, 20),
('SP003', 'Bàn phím cơ', 1, 'Cái', 80, 500000, 750000, 15),
('SP004', 'Giấy A4', 2, 'Ram', 200, 60000, 80000, 30),
('SP005', 'USB 64GB', 3, 'Cái', 60, 120000, 180000, 10);
