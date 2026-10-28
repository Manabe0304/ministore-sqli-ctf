# MiniStore — SQL Injection CTF Lab

> ⚠️ **TUYÊN BỐ GIÁO DỤC / PHẠM VI HỢP PHÁP**
> Ứng dụng này **cố ý** chứa lỗ hổng SQL injection để phục vụ đào tạo / CTF.
> - Chỉ triển khai trong môi trường lab/sandbox được cấp phép.
> - Không deploy cho mục đích khác, không áp dụng kỹ thuật ở đây lên hệ
>   thống không được phép.

MiniStore là một shop demo (Flask + SQLite) chứa đúng **3 kỹ thuật SQL
injection**, mỗi kỹ thuật gắn với **một flag độc lập**:

| Kỹ thuật | Endpoint |
|----------|----------|
| UNION-based | `/products?id=` |
| Boolean-based Blind | `/check?username=` |
| Authentication Bypass | `/login` |

Ứng dụng không hiển thị câu truy vấn SQL hay nội dung lỗi chi tiết ở bất
kỳ đâu — khi `id`/`username` gây lỗi cú pháp, ứng dụng chỉ âm thầm trả về
"không tìm thấy", nên không tồn tại hướng khai thác error-based.

---

## 1. Cấu trúc thư mục

```
ministore-sqli-ctf/
├── Dockerfile
├── requirements.txt
├── docker-compose.yml       # Chay 1 lenh: docker compose up --build
├── app.py                   # 3 route: /products, /check, /login (+dashboard)
├── init_db.py                # Khoi tao CSDL + 3 flag (union/boolean_blind/auth_bypass)
├── exploit.py                # Script tu dong khai thac ca 3 ky thuat
├── run.sh                    # Chay khong can Docker (dev/test)
├── templates/                 # index, product, check, login, dashboard, base...
└── static/
    ├── css/ (bootstrap.min.css, style.css)
    ├── js/main.js              # Hieu ung giao dien
    └── images/
```

**Đóng gói nộp lên hệ thống F-CTF:** nén toàn bộ thư mục này thành `.zip`
— `Dockerfile` ở gốc thư mục.

---

## 2. Lược đồ CSDL (SQLite, `store.db`)

| Bảng       | Cột                                              | Vai trò |
|------------|---------------------------------------------------|---------|
| `users`    | id, username, password, role, email, full_name     | auth bypass, boolean blind |
| `products` | id, name, category, price, description, image      | UNION-based |
| `flags`    | id, code, title, flag                               | **mục tiêu CTF** — 3 flag |

Tài khoản mẫu: `admin / M1n1St0re_Adm1n_2024!` (role `admin`),
`alice/alicepass`, `bob/bobpass123`, `carol/carol!2024` (role `customer`).

---

## 3. Bảng flag theo kỹ thuật

| Kỹ thuật                | Mã nội bộ (cột `code`) | Flag |
|--------------------------|--------------------------|------|
| UNION-based                | `union`           | `FLAG{un10n_b4s3d_d4t4_dump}` |
| Boolean-based Blind         | `boolean_blind`   | `FLAG{b00l34n_bl1nd_1nf3r3nc3}` |
| Authentication Bypass           | `auth_bypass`   | `FLAG{4uth_byp4ss_c0mm3nt_0ut}` |

*(Cột "Mã nội bộ" chỉ là khoá tra cứu trong CSDL/truy vấn khai thác —
không hiển thị ra giao diện hay bất kỳ nơi nào người chơi nhìn thấy.)*

Muốn đổi flag: sửa trong `init_db.py` (hàm `init()`, danh sách
`INSERT INTO flags`) rồi build lại image — CSDL được tạo mới hoàn toàn
mỗi lần container khởi động.

---

## 4. Triển khai

### 4.1 Build & chạy bằng Docker Compose (khuyến nghị — 1 lệnh duy nhất)

```bash
docker compose up --build
# mo http://127.0.0.1:8080
```

`docker-compose.yml` đã cấu hình sẵn đúng các ràng buộc hardening
(`read_only: true`, `tmpfs: /tmp`, `user: "1000"`). Dừng bằng `Ctrl+C`
hoặc `docker compose down`.

### 4.1b Build & chạy bằng `docker run` thủ công (nếu không có Compose)

```bash
docker build -t ministore-sqli-ctf .
docker run --read-only --tmpfs /tmp --user 1000 -p 8080:8080 ministore-sqli-ctf
# mo http://127.0.0.1:8080
```

### 4.2 Chạy không cần Docker (dev nhanh)

```bash
./run.sh
# http://127.0.0.1:8080
```

### 4.3 Kiểm thử tự động

```bash
pip install requests
python3 exploit.py all
```

---

## 5. Reset / dọn dẹp

CSDL được **tạo mới hoàn toàn** mỗi khi container khởi động (`store.db`
nằm trong `/tmp`, là tmpfs). Khi chạy local bằng `run.sh`:

```bash
rm -f store.db && rm -rf .venv
```

---

## 6. Phòng chống (dành cho phần thuyết trình / write-up)

1. **Tham số hoá truy vấn / prepared statements** — biện pháp số một cho
   cả 3 bài (UNION, boolean blind, auth bypass đều do nối chuỗi SQL).
2. Validate & ép kiểu input (id phải là số nguyên).
3. Tắt hiển thị lỗi chi tiết ở production (lab này đã mô phỏng sẵn việc
   ẩn lỗi — đúng thực hành chuẩn).
4. Hash mật khẩu (bcrypt/argon2) thay vì lưu plaintext và so sánh trực
   tiếp trong câu SQL.
5. Giới hạn quyền tài khoản DB theo nguyên tắc least privilege.

Xem `HUONG_DAN_CHAY.md` để biết các bước khai thác chi tiết (writeup/đáp
án) cho từng kỹ thuật.

---

## 7. Các "mồi nhử" (decoy)

Muc tiêu: khiến người chơi phải **tự xác minh** điểm nào thực sự dễ tổn
thương thay vì giả định "cứ thấy tham số GET là thử SQLi". Tất cả mồi
nhử dưới đây **an toàn 100%** (không tạo lỗ hổng):

| Vị trí | Trông giống | Thực tế |
|---|---|---|
| Trang chủ `?q=` | Tìm kiếm theo tên — có vẻ inject được | Dùng `LIKE ?` tham số hoá đầy đủ |
| Trang chủ `?category=` | Lọc theo danh mục | Dùng `= ?` tham số hoá đầy đủ |
| Trang chủ `?sort=` | Sắp xếp theo giá/tên | Whitelist cố định (`SORT_OPTIONS`), không nhận giá trị tuỳ ý |
| `/register` | Có thể nghĩ đây là bài second-order | Ghi an toàn (tham số hoá), không phải lỗ hổng |
| `/cart` — ô "Mã giảm giá" | Trông như có kiểm tra phía server | Chỉ là JS phía client, không hề gọi về server |
| Comment trong `base.html` | `<!-- TODO: go bo endpoint /internal/metrics -->`, `<!-- changelog: da vo hieu hoa /export-db -->` | Các endpoint này **không tồn tại** — chỉ là mồi câu giờ cho ai thích dò `view-source` |

Nếu muốn tăng thêm độ khó, có thể chỉnh `SORT_OPTIONS`/whitelist để
thêm nhiều lựa chọn hơn, hoặc thêm vài trang tĩnh khác (FAQ, chính sách
đổi trả…) theo cùng khuôn mẫu `about.html`/`contact.html`.
