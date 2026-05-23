# 🧾 Aether IoT Labs - Desktop Billing Desk (POS)

> An offline-first, native Python desktop Point of Sale (POS) system designed for 80mm thermal receipt printers. Optimized for keyboard-only operations with robust local SQLite persistence.

---

## 🎨 Design Spec & Key features

- **⌨️ Keyboard-Only Navigation:** Autocomplete input box, arrow-key navigation, instant enter selection, and globally bound F12 checkout.
- **⚡ Offline-First Architecture:** Complete data integrity backed by a local SQLite ledger database (`pos_billing.db`).
- **🏬 Shop Settings Configuration:** Persisted shop metadata populates invoice headers in real-time.
- **📦 Inventory Master Database:** Add, update, search, and delete catalog items with interactive dropdown tax slabs.
- **🛒 Dynamic Sales Checkout:** Real-time billing math engine with CGST/SGST tax back-calculation split (50/50) and flat discounts.
- **🖨️ 80mm Monospace Spooling:** Spools direct to default printing spooler or falls back seamlessly to `receipt.txt` formatting.

---

## 🛠️ Stack & Dependencies

- **GUI Framework:** `customtkinter` (Modern Tkinter dark/light window wrap)
- **Database Engine:** `sqlite3` (Python standard library)
- **Printing API:** `win32print` / `win32ui` (Windows) or `lp` command line spooling utility (macOS / Linux)

---

## 🚀 Setup & Launch

1. **Clone and Install dependencies:**
   ```bash
   git clone https://github.com/harshitchauhann95/bill.git
   cd bill
   pip3 install customtkinter
   ```

2. **Launch the POS Engine:**
   ```bash
   python3 main.py
   ```

---

## ⌨️ Hotkeys Reference

| Key Event | Action | Focus context |
|---|---|---|
| **`F12`** | Save Invoice & Print thermal slip | Global |
| **`Down Arrow`** | Open autocomplete options dropdown | Search Bar |
| **`Enter / Return`** | Add item from autocomplete lists to cart | Search / Dropdown |
| **`+` / `=`** | Increment quantity by 1 | Cart Selected Row |
| **`-` / `_`** | Decrement quantity by 1 (Remove if 0) | Cart Selected Row |

---

**Version:** `v2.0.0` (Python Refactor)  
**License:** MIT
