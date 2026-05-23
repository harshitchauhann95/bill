# 🧾 IoT Billing Machine

> A modular, offline-first, browser-based Point-of-Sale (POS) system for shop owners — featuring shop configuration, inventory management, GST-compliant billing, and 80mm thermal receipt printing.

---

## 🗂️ Module Architecture

| Module              | Branch                    | Status        | Description                         |
|---------------------|---------------------------|---------------|-------------------------------------|
| Shop Configuration  | `feature/shop-setup`      | ✅ Merged     | Shop identity & localStorage layer  |
| Inventory Master    | `feature/inventory-master`| ✅ Merged     | Product CRUD with barcode search    |
| Billing Desk        | `feature/billing-desk`    | ✅ Merged     | Cart engine, GST math, 80mm print   |

---

## 🚀 Local Setup

```bash
git clone https://github.com/harshitchauhann95/bill.git
cd bill
open index.html       # macOS
# OR: xdg-open index.html  # Linux
```

> No build step required. Pure HTML + JS + CSS — runs entirely in the browser.

---

## 🌿 Git-Flow Strategy

```
main              ← Production trunk (no direct commits)
 ├── feature/shop-setup
 ├── feature/inventory-master
 └── feature/billing-desk
```

- **`main`** — pristine, production-verified only
- **`feature/*`** — isolated sprint development
- **All merges** via `--no-ff` to preserve topology

---

## 🧾 Features

- 🏪 **Shop Config** — Name, address, GST number, currency, phone (localStorage)
- 📦 **Inventory Master** — Add / Edit / Delete products, barcode scanner ready
- 🛒 **Billing Desk** — Smart cart, quantity control, discount + 18% GST
- 🖨️ **80mm Thermal Print** — Receipt-optimized CSS for Epson / TVS / Gprinter

---

## 📋 Commit Convention

| Prefix      | Purpose                          |
|-------------|----------------------------------|
| `feat`      | New feature                      |
| `fix`       | Bug fix                          |
| `chore`     | Tooling / scaffolding            |
| `style`     | UI/CSS only, no logic change     |
| `refactor`  | Restructure without behavior δ   |
| `docs`      | Documentation only               |

---

**Version:** `v1.0.0`  
**License:** MIT
