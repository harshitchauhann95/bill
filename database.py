import sqlite3
import os

DB_NAME = "pos_billing.db"

def get_connection():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DB_NAME)

def init_db():
    """Initializes the database schema if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Shop Configuration Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shop_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address1 TEXT NOT NULL,
            address2 TEXT,
            phone TEXT,
            gstin TEXT
        )
    """)
    
    # Insert default shop settings if empty
    cursor.execute("SELECT COUNT(*) FROM shop_config")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO shop_config (name, address1, address2, phone, gstin)
            VALUES ('Aether IoT Labs', '101 Quantum Boulevard', 'Cyber City, Sector 5', '+91 98765 43210', '29AAAAA0000A1Z5')
        """)
    
    # 2. Products Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            tax_rate REAL NOT NULL
        )
    """)
    
    # Insert initial mock products if empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        mock_products = [
            ('Lora Transceiver Node', 850.00, 18.0),
            ('DHT22 Humidity Sensor', 220.00, 12.0),
            ('Raspberry Pi 4 Model B', 4200.00, 18.0),
            ('OLED Display 0.96 inch', 150.00, 5.0),
            ('Jumper Wires Pack', 80.00, 0.0)
        ]
        cursor.executemany("INSERT INTO products (name, price, tax_rate) VALUES (?, ?, ?)", mock_products)

    # 3. Invoices Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            subtotal REAL NOT NULL,
            discount REAL NOT NULL,
            tax REAL NOT NULL,
            total REAL NOT NULL
        )
    """)
    
    # 4. Invoice Items Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            tax_rate REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

# --- Database Operations Helpers ---

def get_shop_config():
    """Fetches the shop config row."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, address1, address2, phone, gstin FROM shop_config LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'name': row[0],
            'address1': row[1],
            'address2': row[2] or '',
            'phone': row[3] or '',
            'gstin': row[4] or ''
        }
    return None

def save_shop_config(name, address1, address2, phone, gstin):
    """Updates or inserts the shop configuration row."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM shop_config LIMIT 1")
        row = cursor.fetchone()
        if row:
            cursor.execute("""
                UPDATE shop_config 
                SET name = ?, address1 = ?, address2 = ?, phone = ?, gstin = ?
                WHERE id = ?
            """, (name, address1, address2, phone, gstin, row[0]))
        else:
            cursor.execute("""
                INSERT INTO shop_config (name, address1, address2, phone, gstin)
                VALUES (?, ?, ?, ?, ?)
            """, (name, address1, address2, phone, gstin))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving shop config: {e}")
        return False
    finally:
        conn.close()

def get_all_products():
    """Fetches all products."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, tax_rate FROM products ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'price': r[2], 'tax_rate': r[3]} for r in rows]

def search_products(query):
    """Searches products by name (case-insensitive substring)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, tax_rate FROM products WHERE name LIKE ? ORDER BY name ASC", (f"%{query}%",))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'price': r[2], 'tax_rate': r[3]} for r in rows]

def add_product(name, price, tax_rate):
    """Inserts a new product into database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, price, tax_rate) VALUES (?, ?, ?)", (name, price, tax_rate))
        conn.commit()
        product_id = cursor.lastrowid
        return product_id
    except sqlite3.IntegrityError:
        return -1 # Unique name constraint violation
    except Exception as e:
        print(f"Database error: {e}")
        return -2
    finally:
        conn.close()

def update_product(product_id, name, price, tax_rate):
    """Updates an existing product in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE products 
            SET name = ?, price = ?, tax_rate = ?
            WHERE id = ?
        """, (name, price, tax_rate, product_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def delete_product(product_id):
    """Deletes a product from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def save_invoice(subtotal, discount, tax, total, cart_items):
    """Saves a complete transaction to invoices and invoice_items tables."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("""
            INSERT INTO invoices (subtotal, discount, tax, total)
            VALUES (?, ?, ?, ?)
        """, (subtotal, discount, tax, total))
        invoice_id = cursor.lastrowid
        
        for item in cart_items:
            cursor.execute("""
                INSERT INTO invoice_items (invoice_id, product_id, product_name, quantity, price, tax_rate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (invoice_id, item['id'], item['name'], item['qty'], item['price'], item['tax_rate']))
            
        cursor.execute("COMMIT")
        return invoice_id
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"Transaction saving failed: {e}")
        return None
    finally:
        conn.close()
