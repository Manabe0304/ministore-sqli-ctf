"""
===========================================================================
 MINISTORE — SQL INJECTION CTF LAB (phien ban rut gon: 3 bai)
===========================================================================
 CANH BAO GIAO DUC:
   - Ung dung nay CO Y chua lo hong SQL injection de phuc vu dao tao / CTF.
   - CHI trien khai trong moi truong lab duoc cap phep (vd: sandbox cua
     F-CTF). KHONG deploy cho muc dich khac, KHONG tan cong he thong
     khong duoc phep.

 3 ky thuat SQLi duoc cai trong 3 route, moi route gan voi MOT flag doc
 lap trong bang `flags`:

   UNION-based             /products?id=
   Boolean-based Blind     /check?username=
   Authentication Bypass   /login

 Cac doan code dung truy van bi loi deu danh dau bang comment "# [VULN]".
 Ung dung KHONG hien thi cau SQL hay noi dung loi chi tiet ra giao dien —
 nguoi choi phai tu suy luan tu hanh vi cua trang (giong trai nghiem CTF
 thuc te hon), va dieu nay cung vo hieu hoa hoan toan huong khai thac
 error-based.

 GHI CHU "GAY NHIEU" (tang do kho / chong doan mo):
   Cac trang /, /register, /about, /contact, /cart la trang NOI DUNG THEM
   cho phong phu, deu dung truy van THAM SO HOA (an toan). Trang chu con
   co o tim kiem (?q=), bo loc danh muc (?category=) va sap xep (?sort=)
   trong NHU co the khai thac duoc nhung thuc te DA duoc tham so hoa day
   du — day la "moi nhu" de nguoi choi ren luyen ky nang phan biet diem
   nao that su de hong, khong phai moi tham so co san deu la cua injection.
===========================================================================
"""
import os
import sqlite3

from flask import Flask, request, redirect, render_template, session, url_for

APP_DIR = os.path.dirname(__file__)
DB_PATH = os.environ.get("DB_PATH", os.path.join(APP_DIR, "store.db"))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ministore-ctf-lab-not-secret")

# Danh sach sap xep hop le (whitelist) cho decoy ?sort= tren trang chu.
SORT_OPTIONS = {
    "newest":     ("Moi nhat",        "id DESC"),
    "price_asc":  ("Gia: thap -> cao", "price ASC"),
    "price_desc": ("Gia: cao -> thap", "price DESC"),
    "name_asc":   ("Ten: A -> Z",      "name ASC"),
}


def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


# ---------------------------------------------------------------------------
# Trang chu — danh sach san pham (shop front), co o tim kiem/bo loc/sap xep.
# CA 3 THAM SO NAY DEU DA THAM SO HOA (an toan) — dong vai tro "moi nhu"
# ben canh diem de hong that su (/products?id=).
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    con = get_db()
    cur = con.cursor()

    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "newest")
    if sort not in SORT_OPTIONS:
        sort = "newest"

    sql = "SELECT id, name, category, price, description, image FROM products WHERE 1=1"
    params = []
    if q:
        sql += " AND name LIKE ?"
        params.append(f"%{q}%")
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += f" ORDER BY {SORT_OPTIONS[sort][1]}"

    cur.execute(sql, params)
    products = cur.fetchall()

    cur.execute("SELECT DISTINCT category FROM products ORDER BY category")
    categories = [r["category"] for r in cur.fetchall()]
    con.close()

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        q=q,
        category=category,
        sort=sort,
        sort_options=SORT_OPTIONS,
        user=session.get("user"),
        role=session.get("role"),
    )


# ---------------------------------------------------------------------------
# UNION-BASED
#     /products?id=1  -> trang chi tiet san pham
#     Loi/ngoai le KHONG duoc hien thi ra giao dien (chi mot thong bao
#     chung chung) -> chi con duong khai thac thuc te la UNION-based.
# ---------------------------------------------------------------------------
@app.route("/products")
def products():
    con = get_db()
    cur = con.cursor()
    rows = []
    pid = request.args.get("id")

    if pid is not None:
        try:
            # [VULN] Noi chuoi truc tiep -> UNION-based SQLi
            query = (
                "SELECT id, name, category, price, description, image "
                f"FROM products WHERE id = {pid}"
            )
            cur.execute(query)
            rows = cur.fetchall()
        except Exception:
            # Khong lo chi tiet loi ra giao dien (chan error-based)
            rows = []
        finally:
            con.close()
    else:
        con.close()

    return render_template("product.html", rows=rows, pid=pid)


# ---------------------------------------------------------------------------
# BOOLEAN-BASED BLIND
#     /check?username=  -> cong cu kiem tra tai khoan thanh vien.
#     Chi tra ve 1 trong 2 trang thai: EXISTS / NOT FOUND.
# ---------------------------------------------------------------------------
@app.route("/check")
def check():
    con = get_db()
    cur = con.cursor()
    result = None
    username = request.args.get("username")

    if username is not None:
        try:
            # [VULN] Noi chuoi -> boolean-blind SQLi
            query = f"SELECT id FROM users WHERE username = '{username}'"
            cur.execute(query)
            result = "TAKEN" if cur.fetchone() else "AVAILABLE"
        except Exception:
            # Nuot loi co y -> blind that su (khong lo thong tin gi khac)
            result = "AVAILABLE"
        finally:
            con.close()
    else:
        con.close()

    return render_template("check.html", result=result, username=username)


# ---------------------------------------------------------------------------
# AUTHENTICATION BYPASS
#     /login -> dang nhap tai khoan khach hang / quan tri
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    message = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        con = get_db()
        cur = con.cursor()
        try:
            # [VULN] Noi chuoi ca username lan password -> auth bypass
            query = (
                "SELECT id, username, role FROM users "
                f"WHERE username = '{username}' AND password = '{password}'"
            )
            cur.execute(query)
            row = cur.fetchone()
            if row:
                session["user"] = row["username"]
                session["role"] = row["role"]
                return redirect(url_for("dashboard"))
            message = "Sai ten dang nhap hoac mat khau."
        except Exception:
            message = "Sai ten dang nhap hoac mat khau."
        finally:
            con.close()

    return render_template("login.html", message=message)


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    flag = None
    if session.get("role") == "admin":
        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT flag FROM flags WHERE code = 'auth_bypass'")
        row = cur.fetchone()
        flag = row["flag"] if row else None
        con.close()
    return render_template("dashboard.html", user=session["user"], role=session.get("role"), flag=flag)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# DANG KY TAI KHOAN — trang noi dung them cho phong phu.
# An toan hoan toan: dung tham so hoa (?), khong tao them lo hong nao.
# (Khac voi ban day du truoc day: trang nay KHONG con dung de minh hoa
# second-order SQLi, chi con la tinh nang dang ky thong thuong.)
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    status, message = None, None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()

        if not username or not password:
            status, message = "danger", "Vui long nhap day du ten dang nhap va mat khau."
        else:
            con = get_db()
            cur = con.cursor()
            try:
                cur.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cur.fetchone():
                    status, message = "danger", "Ten dang nhap nay da duoc su dung."
                else:
                    cur.execute(
                        "INSERT INTO users (username, password, role, email, full_name) "
                        "VALUES (?, ?, 'customer', ?, ?)",
                        (username, password, email or f"{username}@ministore.lab", full_name or username),
                    )
                    con.commit()
                    status, message = "ok", "Dang ky thanh cong! Ban co the dang nhap ngay bay gio."
            finally:
                con.close()

    return render_template("register.html", status=status, message=message)


# ---------------------------------------------------------------------------
# GIOI THIEU / LIEN HE / GIO HANG — trang tinh, khong truy van du lieu nhay
# cam, chi de giao dien phong phu nhu mot shop that.
# ---------------------------------------------------------------------------
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    sent = False
    if request.method == "POST":
        # Khong ghi vao CSDL — chi phan hoi UI, giam dien tich tan cong.
        sent = True
    return render_template("contact.html", sent=sent)


@app.route("/cart")
def cart():
    # Gio hang demo — du lieu tinh, khong lien quan CSDL/session that.
    return render_template("cart.html")


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("[!] Chua co store.db. Chay truoc: python3 init_db.py")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
