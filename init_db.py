"""
init_db.py — Khoi tao CSDL SQLite cho "MiniStore" SQL Injection CTF
(phien ban rut gon: 3 bai — UNION-based, Boolean Blind, Auth Bypass).

Chay lai se xoa va tao moi:
    python3 init_db.py
"""
import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "store.db"))


def init():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.executescript(
        """
        CREATE TABLE users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT NOT NULL,
            password    TEXT NOT NULL,          -- plaintext co y, de minh hoa
            role        TEXT NOT NULL DEFAULT 'customer',
            email       TEXT,
            full_name   TEXT
        );

        CREATE TABLE products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            category    TEXT,
            price       REAL,
            description TEXT,
            image       TEXT
        );

        -- Flags cua tung ky thuat khai thac (muc tieu CTF)
        CREATE TABLE flags (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            code  TEXT UNIQUE NOT NULL,          -- ten ky thuat (slug), dung lam khoa tra cuu
            title TEXT NOT NULL,
            flag  TEXT NOT NULL
        );
        """
    )

    cur.executemany(
        "INSERT INTO users (username, password, role, email, full_name) VALUES (?,?,?,?,?)",
        [
            ("admin",   "M1n1St0re_Adm1n_2024!", "admin",    "admin@ministore.lab",   "Store Administrator"),
            ("alice",   "alicepass",             "customer", "alice@ministore.lab",   "Alice Nguyen"),
            ("bob",     "bobpass123",            "customer", "bob@ministore.lab",     "Bob Tran"),
            ("carol",   "carol!2024",            "customer", "carol@ministore.lab",   "Carol Le"),
        ],
    )

    cur.executemany(
        "INSERT INTO products (name, category, price, description, image) VALUES (?,?,?,?,?)",
        [
            ("Wireless Headphones",   "audio",     59.99,  "Tai nghe khong day, chong on chu dong.",  "product-item1.jpg"),
            ("Smart Watch Pro",       "wearable",  129.00, "Dong ho thong minh theo doi suc khoe.",   "product-item2.jpg"),
            ("Classic Leather Wallet","accessory", 34.50,  "Vi da that, thiet ke toi gian.",          "product-item3.jpg"),
            ("Sunglasses Retro",      "accessory", 22.00,  "Kinh mat chong UV phong cach co dien.",   "product-item4.jpg"),
            ("Canvas Backpack",       "bags",      45.90,  "Balo vai canvas ben, nhieu ngan.",        "product-item5.jpg"),
            ("Running Shoes X1",      "footwear",  79.99,  "Giay chay bo nhe, dem em.",               "product-item6.jpg"),
            ("Minimal Desk Lamp",     "home",      28.00,  "Den ban LED dieu chinh do sang.",         "product-item7.jpg"),
            ("Ceramic Mug Set",       "home",      15.50,  "Bo 2 coc su men trang.",                  "product-item8.jpg"),
            ("Yoga Mat Premium",      "sport",     32.00,  "Tham yoga chong truot, day 6mm.",         "product-item9.jpg"),
            ("Bluetooth Speaker Mini","audio",     39.90,  "Loa bluetooth mini, chong nuoc IPX5.",    "product-item10.jpg"),
        ],
    )

    cur.executemany(
        "INSERT INTO flags (code, title, flag) VALUES (?,?,?)",
        [
            ("union",         "UNION-based",         "FLAG{un10n_b4s3d_d4t4_dump}"),
            ("boolean_blind", "Boolean-based Blind",  "FLAG{b00l34n_bl1nd_1nf3r3nc3}"),
            ("auth_bypass",   "Authentication Bypass","FLAG{4uth_byp4ss_c0mm3nt_0ut}"),
        ],
    )

    con.commit()
    con.close()
    print(f"[+] Da tao CSDL: {DB_PATH}")
    print("[+] Tai khoan admin: admin / M1n1St0re_Adm1n_2024!")
    print("[+] 3 flag da duoc nap vao bang 'flags' (UNION-based, Boolean-based Blind, Authentication Bypass).")


if __name__ == "__main__":
    init()
