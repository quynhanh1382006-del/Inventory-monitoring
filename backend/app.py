import os
from decimal import Decimal
import pymysql
from flask import Flask, jsonify, request, send_from_directory, session
from pymysql.cursors import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


FRONTEND_DIR = os.getenv(
    "FRONTEND_DIR",
    os.path.abspath(os.path.join(BASE_DIR, "..", "frontend")),
)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "dev-only-change-this-secret"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
)

def get_db():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "inventory_db"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def json_value(value):
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Unsupported value: {type(value).__name__}")


def query_all(sql, params=()):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows
    finally:
        conn.close()


def query_one(sql, params=()):
    rows = query_all(sql, params)
    return rows[0] if rows else None


def error(message, status=400):
    return jsonify({"error": message}), status


@app.get("/")
def index():
    if "user_id" not in session:
        return send_from_directory(app.static_folder, "login.html")
    return send_from_directory(app.static_folder, "index.html")





@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    full_name = data.get("full_name", "").strip()
    password = data.get("password", "")

    if len(username) < 3 or len(username) > 50:
        return error("Tên đăng nhập phải có từ 3 đến 50 ký tự")

    if not full_name:
        return error("Vui lòng nhập họ và tên")

    if len(password) < 8:
        return error("Mật khẩu phải có ít nhất 8 ký tự")

    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s",
                    (username,)
                )
                if cursor.fetchone():
                    return error("Tên đăng nhập đã tồn tại")

                cursor.execute(
                    """
                    INSERT INTO users (username, password, full_name, role)
                    VALUES (%s, %s, %s, 'STAFF')
                    """,
                    (
                        username,
                        generate_password_hash(password),
                        full_name
                    )
                )
            conn.commit()

        return jsonify({"message": "Đăng ký thành công"}), 201
    except Exception:
        return error("Không thể đăng ký. Vui lòng kiểm tra kết nối cơ sở dữ liệu", 500)


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = query_one(
        """
        SELECT id, username, password, full_name, role
        FROM users
        WHERE username = %s
        """,
        (username,)
    )

    if not user:
        return error("Tên đăng nhập hoặc mật khẩu không đúng", 401)

    stored_password = user["password"]

    try:
        valid = check_password_hash(stored_password, password)
    except (ValueError, TypeError):
        valid = False

    # Hỗ trợ tài khoản cũ đang lưu mật khẩu dạng văn bản thường.
    if not valid and stored_password == password:
        valid = True
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password = %s WHERE id = %s",
                    (generate_password_hash(password), user["id"])
                )
            conn.commit()

    if not valid:
        return error("Tên đăng nhập hoặc mật khẩu không đúng", 401)

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["full_name"] = user["full_name"]
    session["role"] = user["role"]

    return jsonify({
        "message": "Đăng nhập thành công",
        "user": {
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    })


@app.get("/api/me")
def current_user():
    if "user_id" not in session:
        return error("Bạn chưa đăng nhập", 401)

    return jsonify({
        "user": {
            "username": session["username"],
            "full_name": session["full_name"],
            "role": session["role"]
        }
    })


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Đăng xuất thành công"})
@app.before_request
def require_login():
    public_endpoints = {
        "index",
        "health",
        "register",
        "login",
        "current_user",
        "logout",
    }

    if request.path.startswith("/api/") and request.endpoint not in public_endpoints:
        if "user_id" not in session:
            return error("Vui lòng đăng nhập để tiếp tục", 401)

@app.get("/api/health")
def health():
    try:
        row = query_one("SELECT 1 AS ok")
        return jsonify({"status": "ok", "database": row["ok"] == 1})
    except Exception:
        app.logger.exception("Database health check failed")
        return error("Không thể kết nối cơ sở dữ liệu", 503)


@app.get("/api/dashboard")
def dashboard():
    data = query_one("""
        SELECT
            COUNT(*) AS total_products,
            COALESCE(SUM(quantity), 0) AS total_quantity,
            COALESCE(SUM(
                CASE WHEN quantity <= min_stock THEN 1 ELSE 0 END
            ), 0) AS low_stock
        FROM products
    """)
    suppliers = query_one("SELECT COUNT(*) AS total FROM suppliers")
    value = query_one("""
        SELECT COALESCE(SUM(quantity * import_price), 0) AS stock_value
        FROM products
    """)
    return jsonify({
        **data,
        "total_suppliers": suppliers["total"],
        "stock_value": value["stock_value"],
    })


@app.get("/api/categories")
def categories():
    rows = query_all("SELECT id, name, description FROM categories ORDER BY name")
    return jsonify(rows)


@app.get("/api/suppliers")
def suppliers():
    rows = query_all("""
        SELECT id, name, phone, email, address
        FROM suppliers ORDER BY name
    """)
    return jsonify(rows)


@app.get("/api/products")
def products():
    keyword = request.args.get("q", "").strip()
    sql = """
        SELECT p.id, p.code, p.name, p.category_id, c.name AS category_name,
               p.unit, p.quantity, p.import_price, p.sale_price, p.min_stock
        FROM products p
        JOIN categories c ON c.id = p.category_id
    """
    params = ()
    if keyword:
        sql += " WHERE p.code LIKE %s OR p.name LIKE %s"
        params = (f"%{keyword}%", f"%{keyword}%")
    sql += " ORDER BY p.id DESC"
    return jsonify(query_all(sql, params))


@app.post("/api/products")
def create_product():
    data = request.get_json(silent=True) or {}
    required = ("code", "name", "category_id", "unit")
    if any(not str(data.get(key, "")).strip() for key in required):
        return error("Vui lòng nhập mã, tên, danh mục và đơn vị sản phẩm")

    try:
        quantity = int(data.get("quantity", 0))
        min_stock = int(data.get("min_stock", 0))
        import_price = float(data.get("import_price", 0))
        sale_price = float(data.get("sale_price", 0))
        category_id = int(data["category_id"])
        if min(quantity, min_stock) < 0 or min(import_price, sale_price) < 0:
            return error("Số lượng và giá không được âm")

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO products
                    (code, name, category_id, unit, quantity,
                     import_price, sale_price, min_stock)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data["code"].strip(), data["name"].strip(),
                    category_id, data["unit"].strip(), quantity,
                    import_price, sale_price, min_stock,
                ))
                product_id = cur.lastrowid
            conn.commit()
        finally:
            conn.close()
        return jsonify({"message": "Đã thêm sản phẩm", "id": product_id}), 201
    except (ValueError, TypeError):
        return error("Dữ liệu số không hợp lệ")
    except pymysql.err.IntegrityError:
        return error("Mã sản phẩm đã tồn tại hoặc danh mục không hợp lệ")
    except Exception:
        app.logger.exception("Create product failed")
        return error("Không thể thêm sản phẩm", 500)


@app.put("/api/products/<int:product_id>")
def update_product(product_id):
    data = request.get_json(silent=True) or {}
    required = ("code", "name", "category_id", "unit")
    if any(not str(data.get(key, "")).strip() for key in required):
        return error("Vui lòng nhập mã, tên, danh mục và đơn vị sản phẩm")

    try:
        quantity = int(data.get("quantity", 0))
        min_stock = int(data.get("min_stock", 0))
        import_price = float(data.get("import_price", 0))
        sale_price = float(data.get("sale_price", 0))
        category_id = int(data["category_id"])
        if min(quantity, min_stock) < 0 or min(import_price, sale_price) < 0:
            return error("Số lượng và giá không được âm")

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE products
                    SET code=%s, name=%s, category_id=%s, unit=%s,
                        quantity=%s, import_price=%s, sale_price=%s,
                        min_stock=%s
                    WHERE id=%s
                """, (
                    data["code"].strip(), data["name"].strip(),
                    category_id, data["unit"].strip(), quantity,
                    import_price, sale_price, min_stock, product_id,
                ))
                changed = cur.rowcount
            conn.commit()
        finally:
            conn.close()
        if not changed:
            exists = query_one("SELECT id FROM products WHERE id=%s", (product_id,))
            if not exists:
                return error("Không tìm thấy sản phẩm", 404)
        return jsonify({"message": "Đã cập nhật sản phẩm"})
    except (ValueError, TypeError):
        return error("Dữ liệu số không hợp lệ")
    except pymysql.err.IntegrityError:
        return error("Mã sản phẩm đã tồn tại hoặc danh mục không hợp lệ")
    except Exception:
        app.logger.exception("Update product failed")
        return error("Không thể cập nhật sản phẩm", 500)


@app.delete("/api/products/<int:product_id>")
def delete_product(product_id):
    try:
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM products WHERE id=%s", (product_id,))
                deleted = cur.rowcount
            conn.commit()
        finally:
            conn.close()
        if not deleted:
            return error("Không tìm thấy sản phẩm", 404)
        return jsonify({"message": "Đã xóa sản phẩm"})
    except pymysql.err.IntegrityError:
        return error(
            "Không thể xóa sản phẩm đã có lịch sử nhập hoặc xuất kho", 409
        )
    except Exception:
        app.logger.exception("Delete product failed")
        return error("Không thể xóa sản phẩm", 500)


def process_receipt(kind, data):
    is_import = kind == "import"
    receipt_table = "import_receipts" if is_import else "export_receipts"
    detail_table = "import_details" if is_import else "export_details"
    date_column = "import_date" if is_import else "export_date"
    quantity_key = "quantity"

    code = str(data.get("code", "")).strip()
    details = data.get("details")
    if not code or not isinstance(details, list) or not details:
        return error("Cần mã phiếu và ít nhất một dòng sản phẩm")

    try:
        user_id = int(data.get("user_id", 1))
        conn = get_db()
        try:
            with conn.cursor() as cur:
                if is_import:
                    supplier_id = int(data.get("supplier_id", 0))
                    cur.execute("""
                        INSERT INTO import_receipts
                        (code, supplier_id, user_id, note)
                        VALUES (%s, %s, %s, %s)
                    """, (code, supplier_id, user_id, data.get("note", "")))
                else:
                    cur.execute("""
                        INSERT INTO export_receipts
                        (code, user_id, receiver, note)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        code, user_id, data.get("receiver", ""),
                        data.get("note", ""),
                    ))
                receipt_id = cur.lastrowid

                for item in details:
                    product_id = int(item["product_id"])
                    quantity = int(item[quantity_key])
                    price = float(item.get("unit_price", 0))
                    if quantity <= 0 or price < 0:
                        raise ValueError("Số lượng phải dương và giá không âm")

                    cur.execute(
                        "SELECT quantity FROM products WHERE id=%s FOR UPDATE",
                        (product_id,),
                    )
                    product = cur.fetchone()
                    if not product:
                        raise ValueError(f"Không tìm thấy sản phẩm ID {product_id}")

                    if not is_import and product["quantity"] < quantity:
                        raise ValueError(
                            f"Sản phẩm ID {product_id} không đủ hàng trong kho"
                        )

                    if is_import:
                        cur.execute("""
                            INSERT INTO import_details
                            (import_receipt_id, product_id, quantity, unit_price)
                            VALUES (%s, %s, %s, %s)
                        """, (receipt_id, product_id, quantity, price))
                        cur.execute("""
                            UPDATE products SET quantity=quantity+%s WHERE id=%s
                        """, (quantity, product_id))
                    else:
                        cur.execute("""
                            INSERT INTO export_details
                            (export_receipt_id, product_id, quantity, unit_price)
                            VALUES (%s, %s, %s, %s)
                        """, (receipt_id, product_id, quantity, price))
                        cur.execute("""
                            UPDATE products SET quantity=quantity-%s WHERE id=%s
                        """, (quantity, product_id))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return jsonify({"message": "Đã tạo phiếu", "id": receipt_id}), 201
    except (ValueError, TypeError, KeyError) as exc:
        return error(str(exc))
    except pymysql.err.IntegrityError:
        return error("Mã phiếu bị trùng hoặc nhà cung cấp/người dùng không hợp lệ")
    except Exception:
        app.logger.exception("Receipt creation failed")
        return error("Không thể tạo phiếu", 500)


@app.post("/api/imports")
def create_import():
    return process_receipt("import", request.get_json(silent=True) or {})


@app.post("/api/exports")
def create_export():
    return process_receipt("export", request.get_json(silent=True) or {})


@app.get("/api/history")
def history():
    rows = query_all("""
        SELECT r.code, 'Nhập kho' AS type, r.import_date AS created_at,
               p.name AS product_name, d.quantity, d.unit_price
        FROM import_receipts r
        JOIN import_details d ON d.import_receipt_id = r.id
        JOIN products p ON p.id = d.product_id
        UNION ALL
        SELECT r.code, 'Xuất kho' AS type, r.export_date AS created_at,
               p.name AS product_name, d.quantity, d.unit_price
        FROM export_receipts r
        JOIN export_details d ON d.export_receipt_id = r.id
        JOIN products p ON p.id = d.product_id
        ORDER BY created_at DESC
        LIMIT 100
    """)
    return jsonify(rows)


@app.errorhandler(404)
def not_found(exc):
    if request.path.startswith("/api/"):
        return error("Không tìm thấy API", 404)
    return exc


@app.errorhandler(500)
def internal_error(exc):
    app.logger.exception("Unhandled server error")
    return error("Lỗi máy chủ nội bộ", 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
