import sys
import os
import subprocess
from datetime import datetime

# Monospace width for 80mm receipt printer
RECEIPT_WIDTH = 40

def format_center(text, width=RECEIPT_WIDTH):
    """Centers text within the specified width."""
    text = str(text).strip()
    if len(text) >= width:
        return text[:width]
    return text.center(width)

def format_row(item, qty, amt, width=RECEIPT_WIDTH):
    """Formats a columns row: Left-aligned item name, right-aligned Qty and Amt."""
    # Item takes remaining space, Qty takes 6 chars, Amt takes 10 chars
    qty_str = str(qty)
    amt_str = f"{float(amt):.2f}"
    
    # Space allocation: Item (22 chars), Qty (6 chars), Amt (10 chars) + 2 spaces
    item_width = width - 6 - 10 - 2
    if len(item) > item_width:
        item_name = item[:item_width-1] + "~"
    else:
        item_name = item.ljust(item_width)
        
    return f"{item_name} {qty_str.rjust(5)} {amt_str.rjust(10)}"

def format_summary_line(label, value, width=RECEIPT_WIDTH):
    """Formats a right-aligned key-value line for totals."""
    val_str = f"{float(value):.2f}"
    line = f"{label}: {val_str}"
    return line.rjust(width)

def generate_receipt_string(shop_config, bill_id, cart_items, subtotal, discount, cgst, sgst, total):
    """Generates a structured plain-text receipt aligned to 80mm monospace format."""
    lines = []
    
    # 1. Shop configuration metadata (Centered)
    lines.append(format_center(shop_config['name']))
    if shop_config.get('address1'):
        lines.append(format_center(shop_config['address1']))
    if shop_config.get('address2'):
        lines.append(format_center(shop_config['address2']))
    if shop_config.get('phone'):
        lines.append(format_center(f"Ph: {shop_config['phone']}"))
    if shop_config.get('gstin'):
        lines.append(format_center(f"GSTIN: {shop_config['gstin']}"))
        
    lines.append("")
    lines.append(format_center("RETAIL INVOICE"))
    lines.append("-" * RECEIPT_WIDTH)
    
    # 2. Date & Bill details
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"Date: {timestamp_str}")
    lines.append(f"Bill No: INV-{str(bill_id).zfill(6)}")
    lines.append("-" * RECEIPT_WIDTH)
    
    # 3. Item header
    # Space allocation: Item description (22), Qty (5), Amt (10), plus spaces
    lines.append("Item Description        Qty        Amt")
    lines.append("-" * RECEIPT_WIDTH)
    
    # 4. Item List
    for item in cart_items:
        # If item has a long name, print row
        line_subtotal = item['price'] * item['qty']
        lines.append(format_row(item['name'], item['qty'], line_subtotal))
        
    lines.append("-" * RECEIPT_WIDTH)
    
    # 5. Summary calculations (Right-aligned)
    lines.append(format_summary_line("Subtotal", subtotal))
    if float(discount) > 0:
        lines.append(format_summary_line("Discount", discount))
    lines.append(format_summary_line("CGST Total (9%)", cgst))
    lines.append(format_summary_line("SGST Total (9%)", sgst))
    lines.append("-" * RECEIPT_WIDTH)
    lines.append(format_summary_line("GRAND TOTAL", total))
    lines.append("-" * RECEIPT_WIDTH)
    
    # 6. Footnote
    lines.append("E & O.E".rjust(RECEIPT_WIDTH))
    lines.append("")
    lines.append(format_center("Thank you for shopping!"))
    lines.append(format_center("Powered by IoT Billing POS"))
    lines.append("\n\n\n\n") # Printer paper feed cut spacing
    
    return "\n".join(lines)

def send_to_printer(receipt_text):
    """Sends the formatted receipt buffer to the printer or fallback file."""
    # Write to local receipt.txt fallback first
    fallback_path = os.path.abspath("receipt.txt")
    try:
        with open(fallback_path, "w", encoding="utf-8") as f:
            f.write(receipt_text)
        print(f"Receipt written to {fallback_path}")
    except Exception as e:
        print(f"Failed to write receipt fallback file: {e}")
        
    # Attempt native print based on Platform
    if sys.platform.startswith('win32'):
        try:
            import win32print
            import win32ui
            # Open default printer
            printer_name = win32print.GetDefaultPrinter()
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                # Spool document to printer
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("POS Invoice", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, receipt_text.encode('utf-8'))
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
            return True, "Windows Spooler"
        except Exception as e:
            return False, f"Windows printing failed (spooled to receipt.txt): {e}"
            
    elif sys.platform.startswith('darwin') or sys.platform.startswith('linux'):
        # macOS / Linux: Try printing via 'lp' utility
        try:
            # Check if default printer is set
            process = subprocess.Popen(['lp', fallback_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                return True, "macOS/Linux Spooler via lp"
            else:
                return False, f"lp error: {stderr.decode('utf-8').strip()} (Written to receipt.txt)"
        except Exception as e:
            return False, f"Platform printing command failed: {e} (Written to receipt.txt)"
            
    return True, f"Spelled to receipt.txt fallback successfully."
