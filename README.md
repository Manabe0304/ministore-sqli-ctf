# MiniStore — SQL Injection CTF Lab (bản rút gọn: 3 bài)

> ⚠️ **TUYÊN BỐ GIÁO DỤC / PHẠM VI HỢP PHÁP**
> Ứng dụng này **cố ý** chứa lỗ hổng SQL injection để phục vụ đào tạo / CTF.
> - Chỉ triển khai trong môi trường lab/sandbox được cấp phép.
> - Không deploy cho mục đích khác, không áp dụng kỹ thuật ở đây lên hệ
>   thống không được phép.

MiniStore là một shop demo (Flask + SQLite) chứa **3 kỹ thuật SQL
injection**, mỗi kỹ thuật gắn với **một flag độc lập**:

| Kỹ thuật | Endpoint | Ghi chú |
|----------|----------|---------|
| UNION-based | `/products?id=` | Flag nằm trong bảng `flags`, ẩn giữa nhiều bảng ảo gây nhiễu |
| Boolean-based Blind | `/check?username=` | 2 bước: dump mật khẩu thật của admin, rồi dump flag — cùng một oracle |
| Authentication Bypass | `/login` | Route này chặn sẵn ký tự comment SQL, phải dùng tautology OR |

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
├── init_db.py                # Khoi tao CSDL + 3 flag doc lap (union/boolean_blind/auth_bypass)
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

### Bảng thật

| Bảng       | Cột                                              | Vai trò |
|------------|---------------------------------------------------|---------|
| `users`    | id, username, password, role, email, full_name     | auth bypass; mật khẩu admin là mục tiêu bước 1 của Boolean Blind |
| `products` | id, name, category, price, description, image      | bề mặt UNION-based (điểm inject) |
| `flags`    | id, code, title, flag                               | **mục tiêu CTF** — 3 flag độc lập |

Tài khoản mẫu: `admin / M1n1St0re_Adm1n_2024!` (role `admin`),
`alice/alicepass`, `bob/bobpass123`, `carol/carol!2024` (role `customer`).

### Bảng ảo gây nhiễu (chỉ để tăng độ khó khâu recon UNION-based)

| Bảng ảo | Vì sao là bẫy |
|---|---|
| `flags_backup` | Cùng schema với `flags` thật nhưng chứa giá trị SAI (bản "rotate" cũ) |
| `vault` | Có dòng dữ liệu đúng định dạng `FLAG{...}` nhưng là flag GIẢ |
| `tokens` | Chuỗi ngẫu nhiên vô nghĩa |
| `admin_backup` | Tài khoản admin CŨ, không đăng nhập được, không liên quan |
| `config` | Cấu hình hệ thống thông thường, vô hại |

---

Muốn đổi flag: sửa `init_db.py` (`INSERT INTO flags`), build lại —
CSDL được tạo mới hoàn toàn mỗi lần container khởi động.

Xem `HUONG_DAN_CHAY.md` để biết các bước khai thác chi tiết (writeup/đáp
án) cho từng kỹ thuật.

---

## 3. Triển khai

### 3.1 Docker Compose (khuyến nghị)

```bash
docker compose up --build
# mo http://127.0.0.1:8080
```

`docker-compose.yml` đã cấu hình sẵn hardening (`read_only: true`,
`tmpfs: /tmp`, `user: "1000"`). Dừng bằng `Ctrl+C` hoặc `docker compose down`.

### 3.1b `docker run` thủ công

```bash
docker build -t ministore-sqli-ctf .
docker run --read-only --tmpfs /tmp --user 1000 -p 8080:8080 ministore-sqli-ctf
```

### 3.2 Không cần Docker (dev nhanh)

```bash
./run.sh
# http://127.0.0.1:80800
```

### 3.3 Kiểm thử tự động

```bash
pip install requests
python3 exploit.py all --base http://127.0.0.1:8080
```

---

## 4. Reset / dọn dẹp

CSDL được tạo mới hoàn toàn mỗi khi container khởi động (`store.db` nằm
trong `/tmp`, là tmpfs). Khi chạy local bằng `run.sh`:

```bash
rm -f store.db && rm -rf .venv
```

---

## 5. Phòng chống (dành cho phần thuyết trình / write-up)

1. **Tham số hoá truy vấn / prepared statements** — biện pháp số một,
   triệt để duy nhất cho cả 3 bài. Bộ lọc chặn comment ở `/login` chỉ
   minh hoạ rằng **blacklist không bao giờ đủ** (vẫn bị bypass bằng
   tautology).
2. Validate & ép kiểu input (id phải là số nguyên).
3. Tắt hiển thị lỗi chi tiết ở production.
4. Hash mật khẩu (bcrypt/argon2) thay vì lưu plaintext — nếu làm đúng,
   bài Boolean Blind sẽ không thể dump được mật khẩu gốc dù vẫn còn lỗ
   hổng injection.
5. Giới hạn quyền tài khoản DB theo nguyên tắc least privilege.
6. Giới hạn số lần đăng nhập sai (rate limiting / account lockout).

---

## 6. Các "mồi nhử" (decoy)

Mục tiêu: khiến người chơi phải **tự xác minh** điểm nào thực sự dễ tổn
thương. Tất cả mồi nhử dưới đây **an toàn 100%**:

| Vị trí | Trông giống | Thực tế |
|---|---|---|
| Trang chủ `?q=` | Tìm kiếm theo tên | Dùng `LIKE ?` tham số hoá đầy đủ |
| Trang chủ `?category=` | Lọc theo danh mục | Dùng `= ?` tham số hoá đầy đủ |
| Trang chủ `?sort=` | Sắp xếp theo giá/tên | Whitelist cố định (`SORT_OPTIONS`) |
| `/register` | Có thể nghĩ là second-order SQLi | Ghi an toàn (tham số hoá) |
| `/cart` — "Mã giảm giá" | Trông như có kiểm tra phía server | Chỉ là JS phía client |
| Comment trong `base.html` | `<!-- TODO: go bo endpoint /internal/metrics -->` | Endpoint không tồn tại |
| Bảng `flags_backup` | Cùng cấu trúc bảng `flags` thật | Chứa giá trị SAI |
| Bảng `vault` | Dòng dữ liệu đúng định dạng `FLAG{...}` | Là flag GIẢ |
| Payload `admin' -- ` ở `/login` | Từng hoạt động ở bản trước | Phải dùng tautology OR |
