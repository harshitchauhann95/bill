import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import sqlite3
import database
import printer

# --- UI Customizations ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class POSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("Aether IoT Labs - Billing Desk (Desktop POS)")
        self.geometry("1100x700")
        self.minimum_size = (1000, 650)
        
        # Initialize Database
        try:
            database.init_db()
        except Exception as e:
            self.show_status_message(f"DB Init Failed: {e}", "red")

        # Application state
        self.cart_items = [] # list of dicts: {'id': id, 'name': name, 'price': price, 'tax_rate': tax_rate, 'qty': qty}
        self.current_selected_prod_id = None # for inventory edit mode
        self.search_matches = [] # list of matches for autocomplete
        self.active_search_index = -1
        
        # Configure Grid Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Set up styles for native Ttk widgets (like Treeview)
        self.configure_treeview_styles()
        
        # Create Tab View Container
        self.tabview = ctk.CTkTabview(self, segmented_button_fg_color="#0f1626", segmented_button_selected_color="#00d2ff", segmented_button_selected_hover_color="#00b4db")
        self.tabview.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        self.tab_billing = self.tabview.add("🛒 Daily Billing")
        self.tab_inventory = self.tabview.add("📦 Inventory Master")
        self.tab_settings = self.tabview.add("⚙️ Shop Settings")
        
        # Build Panels
        self.build_billing_panel()
        self.build_inventory_panel()
        self.build_settings_panel()
        
        # Global Event Bindings
        self.bind("<F12>", lambda event: self.trigger_print_routine())
        self.bind("<KeyPress>", self.handle_global_key_press)
        
        # Load startup configurations
        self.load_shop_config_to_ui()
        self.refresh_inventory_grid()
        self.refresh_billing_catalog_items()
        
        # Put focus on billing search field on launch
        self.after(200, lambda: self.billing_search_entry.focus())

    def configure_treeview_styles(self):
        """Styles the native ttk.Treeview to seamlessly match the dark glassmorphism design."""
        style = ttk.Style()
        style.theme_use("default")
        
        # Table Styling
        style.configure("Treeview",
            background="#17223b",
            foreground="#f8f9fa",
            rowheight=35,
            fieldbackground="#17223b",
            font=("Outfit", 11),
            borderwidth=0
        )
        style.map("Treeview",
            background=[("selected", "#00d2ff")],
            foreground=[("selected", "#080c14")]
        )
        
        # Header Styling
        style.configure("Treeview.Heading",
            background="#0f1626",
            foreground="#8d99ae",
            font=("Outfit", 10, "bold"),
            borderwidth=0,
            relief="flat"
        )
        style.map("Treeview.Heading",
            background=[("active", "#17223b")],
            foreground=[("active", "#00d2ff")]
        )

    # =========================================================================
    # 🛒 PANEL 1: DAILY BILLING
    # =========================================================================
    def build_billing_panel(self):
        self.tab_billing.grid_rowconfigure(0, weight=1)
        self.tab_billing.grid_columnconfigure(0, weight=3) # Cart & Inputs
        self.tab_billing.grid_columnconfigure(1, weight=2) # Totals & Controls
        
        # --- LEFT SIDE: CART & INPUTS ---
        left_frame = ctk.CTkFrame(self.tab_billing, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Autocomplete search bar container
        search_container = ctk.CTkFrame(left_frame, fg_color="#0f1626", border_width=1, border_color="#20293a")
        search_container.grid(row=0, column=0, padx=0, pady=(0, 10), sticky="ew")
        search_container.grid_columnconfigure(0, weight=1)
        
        search_label = ctk.CTkLabel(search_container, text="🔍 SCAN OR SEARCH PRODUCT NAME (Press Down to list / Enter to add)", font=("Outfit", 10, "bold"), text_color="#8d99ae")
        search_label.grid(row=0, column=0, padx=12, pady=(8, 2), sticky="w")
        
        self.billing_search_entry = ctk.CTkEntry(search_container, height=45, placeholder_text="Type product name or scan barcode...", font=("Outfit", 14), fg_color="#17223b", border_color="#253047")
        self.billing_search_entry.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")
        
        # Bind keyboard search events
        self.billing_search_entry.bind("<KeyRelease>", self.on_billing_search_key_release)
        self.billing_search_entry.bind("<Down>", self.focus_billing_search_listbox)
        self.billing_search_entry.bind("<Return>", self.on_billing_search_entry_enter)
        
        # Embedded Autocomplete Dropdown Listbox
        self.billing_listbox_frame = ctk.CTkFrame(left_frame, fg_color="#17223b", border_width=1, border_color="#00d2ff")
        self.billing_listbox = tk.Listbox(
            self.billing_listbox_frame,
            bg="#17223b",
            fg="#f8f9fa",
            selectbackground="#00d2ff",
            selectforeground="#080c14",
            font=("Outfit", 12),
            bd=0,
            highlightthickness=0,
            height=6
        )
        self.billing_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.billing_listbox.bind("<Return>", self.on_billing_listbox_select)
        self.billing_listbox.bind("<Double-Button-1>", self.on_billing_listbox_select)
        self.billing_listbox.bind("<Escape>", self.hide_billing_search_listbox)
        
        # Active Cart Grid
        cart_card = ctk.CTkFrame(left_frame, fg_color="#0f1626", border_width=1, border_color="#20293a")
        cart_card.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        cart_card.grid_rowconfigure(1, weight=1)
        cart_card.grid_columnconfigure(0, weight=1)
        
        cart_title = ctk.CTkLabel(cart_card, text="🛒 ACTIVE SALES CART", font=("Outfit", 14, "bold"), text_color="#00d2ff")
        cart_title.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")
        
        # Treeview setup
        self.cart_tree = ttk.Treeview(cart_card, columns=("name", "qty", "price", "total"), show="headings")
        self.cart_tree.heading("name", text="Item Name")
        self.cart_tree.heading("qty", text="Quantity")
        self.cart_tree.heading("price", text="Unit Price")
        self.cart_tree.heading("total", text="Total Price")
        
        self.cart_tree.column("name", width=300, anchor="w")
        self.cart_tree.column("qty", width=90, anchor="center")
        self.cart_tree.column("price", width=120, anchor="e")
        self.cart_tree.column("total", width=140, anchor="e")
        
        self.cart_tree.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Scrollbar for cart
        cart_scroll = ttk.Scrollbar(cart_card, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scroll.set)
        cart_scroll.grid(row=1, column=1, sticky="ns", pady=(0, 15), padx=(0, 5))
        
        # --- RIGHT SIDE: SUMMARY MATHS & CONTROLS ---
        right_frame = ctk.CTkFrame(self.tab_billing, fg_color="#0f1626", border_width=1, border_color="#20293a")
        right_frame.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        right_frame.grid_rowconfigure(4, weight=1) # expand empty space
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Panel Title
        right_title = ctk.CTkLabel(right_frame, text="🧾 BILL DETAILS & SUMMARY", font=("Outfit", 16, "bold"), text_color="#9d4edd")
        right_title.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # Summary Grid details
        summary_inner = ctk.CTkFrame(right_frame, fg_color="transparent")
        summary_inner.grid(row=1, column=0, padx=20, pady=0, sticky="ew")
        summary_inner.grid_columnconfigure(1, weight=1)
        
        # Subtotal
        ctk.CTkLabel(summary_inner, text="Sub-Total:", font=("Outfit", 13, "bold"), text_color="#8d99ae").grid(row=0, column=0, sticky="w", pady=8)
        self.lbl_subtotal = ctk.CTkLabel(summary_inner, text="₹0.00", font=("Outfit", 15, "bold"), text_color="#f8f9fa")
        self.lbl_subtotal.grid(row=0, column=1, sticky="e", pady=8)
        
        # Flat Discount entry
        ctk.CTkLabel(summary_inner, text="Flat Discount (₹):", font=("Outfit", 13, "bold"), text_color="#8d99ae").grid(row=1, column=0, sticky="w", pady=8)
        self.ent_discount = ctk.CTkEntry(summary_inner, width=120, placeholder_text="0.00", font=("Outfit", 13), justify="right")
        self.ent_discount.insert(0, "0")
        self.ent_discount.grid(row=1, column=1, sticky="e", pady=8)
        self.ent_discount.bind("<KeyRelease>", lambda e: self.update_calculations())
        
        # Tax details (Split CGST/SGST)
        ctk.CTkLabel(summary_inner, text="CGST Total:", font=("Outfit", 12), text_color="#8d99ae").grid(row=2, column=0, sticky="w", pady=5)
        self.lbl_cgst = ctk.CTkLabel(summary_inner, text="₹0.00", font=("Outfit", 13), text_color="#f8f9fa")
        self.lbl_cgst.grid(row=2, column=1, sticky="e", pady=5)
        
        ctk.CTkLabel(summary_inner, text="SGST Total:", font=("Outfit", 12), text_color="#8d99ae").grid(row=3, column=0, sticky="w", pady=5)
        self.lbl_sgst = ctk.CTkLabel(summary_inner, text="₹0.00", font=("Outfit", 13), text_color="#f8f9fa")
        self.lbl_sgst.grid(row=3, column=1, sticky="e", pady=5)
        
        # Divider line
        divider = ctk.CTkFrame(right_frame, height=2, fg_color="#20293a")
        divider.grid(row=2, column=0, padx=20, pady=15, sticky="ew")
        
        # Grand Total Display
        totals_box = ctk.CTkFrame(right_frame, fg_color="#0e1c31", border_width=1, border_color="#0d3a51")
        totals_box.grid(row=3, column=0, padx=20, pady=0, sticky="ew")
        totals_box.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(totals_box, text="GRAND TOTAL:", font=("Outfit", 16, "bold"), text_color="#00d2ff").grid(row=0, column=0, padx=15, pady=15, sticky="w")
        self.lbl_grand_total = ctk.CTkLabel(totals_box, text="₹0.00", font=("Outfit", 20, "bold"), text_color="#00d2ff")
        self.lbl_grand_total.grid(row=0, column=1, padx=15, pady=15, sticky="e")
        
        # Footer Action buttons
        actions_inner = ctk.CTkFrame(right_frame, fg_color="transparent")
        actions_inner.grid(row=5, column=0, padx=20, pady=20, sticky="ew")
        actions_inner.grid_columnconfigure(0, weight=1)
        
        # Prominent Print button
        self.btn_print_bill = ctk.CTkButton(
            actions_inner,
            text="🖨️ SAVE & PRINT BILL (F12)",
            height=50,
            font=("Outfit", 14, "bold"),
            fg_color=("#9d4edd", "#8035c9"),
            hover_color="#9d4edd",
            command=self.trigger_print_routine
        )
        self.btn_print_bill.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.btn_clear_cart = ctk.CTkButton(
            actions_inner,
            text="🗑️ Clear Sales Session",
            height=35,
            font=("Outfit", 12, "bold"),
            fg_color="transparent",
            border_width=1,
            border_color="#600f27",
            hover_color="#220e18",
            text_color="#d90429",
            command=self.clear_cart_session
        )
        self.btn_clear_cart.grid(row=1, column=0, sticky="ew")
        
        # Status Label bar for quick error/success notifications
        self.lbl_billing_status = ctk.CTkLabel(right_frame, text="Ready", font=("Outfit", 11), text_color="#8d99ae")
        self.lbl_billing_status.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")

    # =========================================================================
    # 📦 PANEL 2: INVENTORY MASTER
    # =========================================================================
    def build_inventory_panel(self):
        self.tab_inventory.grid_rowconfigure(0, weight=1)
        self.tab_inventory.grid_columnconfigure(0, weight=2) # Form Editor
        self.tab_inventory.grid_columnconfigure(1, weight=3) # Product list
        
        # --- LEFT SIDE: ADD/EDIT FORM ---
        form_frame = ctk.CTkFrame(self.tab_inventory, fg_color="#0f1626", border_width=1, border_color="#20293a")
        form_frame.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        form_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_inv_form_title = ctk.CTkLabel(form_frame, text="📦 ADD PRODUCT DATABASE", font=("Outfit", 16, "bold"), text_color="#00d2ff")
        self.lbl_inv_form_title.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # Name Entry
        ctk.CTkLabel(form_frame, text="Product Name", font=("Outfit", 11, "bold"), text_color="#8d99ae").grid(row=1, column=0, padx=20, pady=(10, 2), sticky="w")
        self.ent_prod_name = ctk.CTkEntry(form_frame, height=35, placeholder_text="e.g. Lora Sensor Module", font=("Outfit", 12))
        self.ent_prod_name.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Price Entry
        ctk.CTkLabel(form_frame, text="Selling Price (MRP)", font=("Outfit", 11, "bold"), text_color="#8d99ae").grid(row=3, column=0, padx=20, pady=(10, 2), sticky="w")
        self.ent_prod_price = ctk.CTkEntry(form_frame, height=35, placeholder_text="0.00", font=("Outfit", 12))
        self.ent_prod_price.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Tax Slab Dropdown
        ctk.CTkLabel(form_frame, text="Tax Slab (GST %)", font=("Outfit", 11, "bold"), text_color="#8d99ae").grid(row=5, column=0, padx=20, pady=(10, 2), sticky="w")
        self.cmb_prod_tax = ctk.CTkComboBox(form_frame, height=35, values=["0.0", "5.0", "12.0", "18.0", "28.0"], font=("Outfit", 12), state="readonly")
        self.cmb_prod_tax.set("18.0")
        self.cmb_prod_tax.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Form buttons row
        btn_inner = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_inner.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
        btn_inner.grid_columnconfigure(0, weight=1)
        btn_inner.grid_columnconfigure(1, weight=1)
        
        self.btn_save_prod = ctk.CTkButton(btn_inner, text="💾 Save Product", font=("Outfit", 12, "bold"), fg_color="#38b000", hover_color="#38b000", command=self.on_inventory_save_click)
        self.btn_save_prod.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.btn_cancel_prod_edit = ctk.CTkButton(btn_inner, text="Cancel", font=("Outfit", 12), fg_color="transparent", border_width=1, border_color="#334155", text_color="#f8f9fa", command=self.exit_inventory_edit_mode)
        self.btn_cancel_prod_edit.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        self.btn_cancel_prod_edit.grid_remove() # Hidden by default
        
        # --- RIGHT SIDE: DATABASE LIST & FILTER ---
        grid_frame = ctk.CTkFrame(self.tab_inventory, fg_color="#0f1626", border_width=1, border_color="#20293a")
        grid_frame.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        grid_frame.grid_rowconfigure(2, weight=1)
        grid_frame.grid_columnconfigure(0, weight=1)
        
        # Filter controls
        filter_inner = ctk.CTkFrame(grid_frame, fg_color="transparent")
        filter_inner.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        filter_inner.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(filter_inner, text="🔍 Search Filter:", font=("Outfit", 12, "bold"), text_color="#8d99ae").grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.ent_inventory_search = ctk.CTkEntry(filter_inner, height=35, placeholder_text="Type product name to filter database...")
        self.ent_inventory_search.grid(row=0, column=1, sticky="ew")
        self.ent_inventory_search.bind("<KeyRelease>", lambda e: self.refresh_inventory_grid(self.ent_inventory_search.value if hasattr(self.ent_inventory_search, 'value') else self.ent_inventory_search.get()))
        
        # Treeview grid
        self.inv_tree = ttk.Treeview(grid_frame, columns=("id", "name", "price", "tax"), show="headings")
        self.inv_tree.heading("id", text="ID")
        self.inv_tree.heading("name", text="Product Name")
        self.inv_tree.heading("price", text="Price (₹)")
        self.inv_tree.heading("tax", text="Tax (%)")
        
        self.inv_tree.column("id", width=60, anchor="center")
        self.inv_tree.column("name", width=250, anchor="w")
        self.inv_tree.column("price", width=120, anchor="e")
        self.inv_tree.column("tax", width=80, anchor="center")
        
        self.inv_tree.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="nsew")
        
        # Scrollbar for grid
        inv_scroll = ttk.Scrollbar(grid_frame, orient="vertical", command=self.inv_tree.yview)
        self.inv_tree.configure(yscrollcommand=inv_scroll.set)
        inv_scroll.grid(row=2, column=1, sticky="ns", pady=(0, 15), padx=(0, 10))
        
        # Action controls below database grid
        grid_actions = ctk.CTkFrame(grid_frame, fg_color="transparent")
        grid_actions.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        grid_actions.grid_columnconfigure(0, weight=1)
        grid_actions.grid_columnconfigure(1, weight=1)
        
        self.btn_edit_selected = ctk.CTkButton(grid_actions, text="✏️ Edit Selected", font=("Outfit", 12, "bold"), fg_color="#00d2ff", text_color="#080c14", hover_color="#00b4db", command=self.on_inventory_edit_click)
        self.btn_edit_selected.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.btn_delete_selected = ctk.CTkButton(grid_actions, text="🗑️ Delete Selected", font=("Outfit", 12, "bold"), fg_color="transparent", border_width=1, border_color="#d90429", text_color="#d90429", hover_color="#220e18", command=self.on_inventory_delete_click)
        self.btn_delete_selected.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        # Status Label bar for inventory
        self.lbl_inv_status = ctk.CTkLabel(grid_frame, text="Ready", font=("Outfit", 11), text_color="#8d99ae")
        self.lbl_inv_status.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")

    # =========================================================================
    # ⚙️ PANEL 3: SHOP CONFIGURATION
    # =========================================================================
    def build_settings_panel(self):
        self.tab_settings.grid_rowconfigure(0, weight=1)
        self.tab_settings.grid_columnconfigure(0, weight=1)
        
        container = ctk.CTkFrame(self.tab_settings, fg_color="#0f1626", border_width=1, border_color="#20293a")
        container.grid(row=0, column=0, padx=50, pady=30, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        
        # Panel Title
        ctk.CTkLabel(container, text="⚙️ SHOP CONFIGURATION SETTINGS", font=("Outfit", 16, "bold"), text_color="#00d2ff").grid(row=0, column=0, columnspan=2, padx=30, pady=25, sticky="w")
        
        # Shop Name
        ctk.CTkLabel(container, text="Shop / Company Name", font=("Outfit", 11, "bold"), text_color="#8d99ae").grid(row=1, column=0, padx=30, pady=(10, 2), sticky="w")
        self.ent_shop_name = ctk.CTkEntry(container, height=35, font=("Outfit", 12))
        self.ent_shop_name.grid(row=2, column=0, columnspan=2, padx=30, pady=(0, 10), sticky="ew")
        
        # Address Line 1
        ctk.CTkLabel(container, text="Address Line 1", font=("Outfit", 11, "bold"), text_color="#8d99ae").grid(row=3, column=0, padx=30, pady=(10, 2), sticky="w")
        self.ent_shop_addr1 = ctk.CTkEntry(container, height=35, font=("Outfit", 12))
        self.ent_shop_addr1.grid(row=4, column=0, columnspan=2, padx=30, pady=(0, 10), sticky="ew")
        
        # Address Line 2
        ctk.CTkLabel(container, text="Address Line 2", font=("Outfit", 11, "bold"), text_color="#8d99ae").grid(row=5, column=0, padx=30, pady=(10, 2), sticky="w")
        self.ent_shop_addr2 = ctk.CTkEntry(container, height=35, font=("Outfit", 12))
        self.ent_shop_addr2.grid(row=6, column=0, columnspan=2, padx=30, pady=(0, 10), sticky="ew")
        
        # Phone & GSTIN
        ctk.CTkLabel(container, text="Phone Number", font=("Outfit", 11, "bold"), text_color="#8d99ae").grid(row=7, column=0, padx=30, pady=(10, 2), sticky="w")
        self.ent_shop_phone = ctk.CTkEntry(container, height=35, font=("Outfit", 12))
        self.ent_shop_phone.grid(row=8, column=0, padx=30, pady=(0, 20), sticky="ew")
        
        ctk.CTkLabel(container, text="GSTIN / Tax ID", font=("Outfit", 11, "bold"), text_color="#8d99ae").grid(row=7, column=1, padx=30, pady=(10, 2), sticky="w")
        self.ent_shop_gstin = ctk.CTkEntry(container, height=35, font=("Outfit", 12))
        self.ent_shop_gstin.grid(row=8, column=1, padx=30, pady=(0, 20), sticky="ew")
        
        # Save Settings
        self.btn_save_config = ctk.CTkButton(container, text="💾 Save Configuration", height=45, font=("Outfit", 13, "bold"), fg_color="#38b000", hover_color="#38b000", command=self.on_shop_config_save_click)
        self.btn_save_config.grid(row=9, column=0, columnspan=2, padx=30, pady=(10, 20), sticky="ew")
        
        # Status Label bar for settings
        self.lbl_settings_status = ctk.CTkLabel(container, text="Ready", font=("Outfit", 11), text_color="#8d99ae")
        self.lbl_settings_status.grid(row=10, column=0, columnspan=2, padx=30, pady=(0, 10), sticky="ew")

    # =========================================================================
    # ⚙️ GLOBAL & HELPER LOGICS
    # =========================================================================
    def show_status_message(self, message, color="green", panel="billing"):
        """Displays status feedback text on the active dashboard frame."""
        status_label = self.lbl_billing_status
        if panel == "inventory":
            status_label = self.lbl_inv_status
        elif panel == "settings":
            status_label = self.lbl_settings_status
            
        color_hex = "#38b000" if color == "green" else "#d90429"
        status_label.configure(text=message, text_color=color_hex)
        
        # Reset message after 4 seconds
        self.after(4000, lambda: status_label.configure(text="Ready", text_color="#8d99ae"))

    def handle_global_key_press(self, event):
        """Processes global hotkeys. E.g., +/- to update active cart item quantities."""
        # Find which widget has focus
        focused = self.focus_get()
        
        # If user is currently typing in an input text field, bypass hotkey intercept
        if isinstance(focused, (ctk.CTkEntry, tk.Entry, tk.Text)):
            return
            
        # Determine active tab
        active_tab = self.tabview.get()
        if active_tab == "🛒 Daily Billing":
            # Target keys for quantity operations
            if event.char in ('+', '='):
                self.increment_selected_cart_qty()
            elif event.char in ('-', '_'):
                self.decrement_selected_cart_qty()

    # =========================================================================
    # 🛒 DAILY BILLING RUNTIME LOGIC
    # =========================================================================
    def on_billing_search_key_release(self, event):
        """Filters autocomplete match selections as the cashier types."""
        if event.keysym in ("Down", "Up", "Return", "Escape"):
            return # Process separately or ignore key release
            
        query = self.billing_search_entry.get().strip()
        if not query:
            self.hide_billing_search_listbox()
            return
            
        try:
            self.search_matches = database.search_products(query)
            if self.search_matches:
                self.billing_listbox.delete(0, tk.END)
                for prod in self.search_matches:
                    tax_indicator = f" (GST {prod['tax_rate']}%)"
                    self.billing_listbox.insert(tk.END, f"{prod['name']} - ₹{prod['price']:.2f}{tax_indicator}")
                
                # Show listbox dropdown below entry
                self.show_billing_search_listbox()
            else:
                self.hide_billing_search_listbox()
        except Exception as e:
            self.show_status_message(f"Search Failed: {e}", "red")

    def show_billing_search_listbox(self):
        """Displays the autocomplete product popup listbox."""
        # Retrieve placement position
        x = self.billing_search_entry.winfo_x()
        y = self.billing_search_entry.winfo_y() + self.billing_search_entry.winfo_height() + 5
        w = self.billing_search_entry.winfo_width()
        
        self.billing_listbox_frame.place(x=x, y=y, width=w, height=180)
        self.billing_listbox_frame.lift()

    def hide_billing_search_listbox(self, event=None):
        """Hides the autocomplete listbox frame."""
        self.billing_listbox_frame.place_forget()
        self.active_search_index = -1

    def focus_billing_search_listbox(self, event):
        """Sets window focus to the autocomplete listbox row selection."""
        if self.billing_listbox_frame.winfo_matched_size or self.search_matches:
            self.billing_listbox.focus_set()
            if self.billing_listbox.size() > 0:
                self.billing_listbox.selection_clear(0, tk.END)
                self.billing_listbox.selection_set(0)
                self.billing_listbox.see(0)

    def on_billing_search_entry_enter(self, event):
        """Handles enter keypress. Adds exact match or top filtered item instantly."""
        query = self.billing_search_entry.get().strip()
        if not query:
            return
            
        # Try checking if listbox has an active selection or if there is a matching list
        if self.search_matches:
            # Add top matched item instantly
            self.add_product_to_cart(self.search_matches[0])
            self.billing_search_entry.delete(0, tk.END)
            self.hide_billing_search_listbox()
        else:
            self.show_status_message("Item not found in catalog", "red")

    def on_billing_listbox_select(self, event):
        """Adds selected product row from listbox to cart."""
        selections = self.billing_listbox.curselection()
        if selections:
            index = selections[0]
            product = self.search_matches[index]
            self.add_product_to_cart(product)
            
            # Clear search bar and reset focus
            self.billing_search_entry.delete(0, tk.END)
            self.hide_billing_search_listbox()
            self.billing_search_entry.focus()

    def add_product_to_cart(self, product):
        """Appends selected item to cart array, matching database attributes."""
        # Check if already in cart
        for item in self.cart_items:
            if item['id'] == product['id']:
                item['qty'] += 1
                self.refresh_cart_grid()
                self.update_calculations()
                self.show_status_message(f"Incremented: {product['name']}")
                return
                
        # Append as new line item
        self.cart_items.append({
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'tax_rate': product['tax_rate'],
            'qty': 1
        })
        self.refresh_cart_grid()
        self.update_calculations()
        self.show_status_message(f"Added: {product['name']}")

    def refresh_cart_grid(self):
        """Renders current active cart rows to the Treeview."""
        # Clear current rows
        for r in self.cart_tree.get_children():
            self.cart_tree.delete(r)
            
        for i, item in enumerate(self.cart_items):
            total_price = item['price'] * item['qty']
            self.cart_tree.insert(
                "",
                "end",
                iid=str(i),
                values=(item['name'], item['qty'], f"₹{item['price']:.2f}", f"₹{total_price:.2f}")
            )

    def increment_selected_cart_qty(self):
        """Increments quantity of currently highlighted cart item in Treeview."""
        selected = self.cart_tree.selection()
        if not selected:
            return
        index = int(selected[0])
        self.cart_items[index]['qty'] += 1
        self.refresh_cart_grid()
        self.update_calculations()
        # Keep item selected
        self.cart_tree.selection_set(str(index))

    def decrement_selected_cart_qty(self):
        """Decrements quantity or deletes item if qty reaches zero."""
        selected = self.cart_tree.selection()
        if not selected:
            return
        index = int(selected[0])
        item = self.cart_items[index]
        if item['qty'] > 1:
            item['qty'] -= 1
            self.refresh_cart_grid()
            self.update_calculations()
            self.cart_tree.selection_set(str(index))
        else:
            del self.cart_items[index]
            self.refresh_cart_grid()
            self.update_calculations()

    def update_calculations(self):
        """Runs the Real-Time POS Math Engine on cart list details."""
        subtotal = 0.0
        total_tax_pool = 0.0
        
        # Calculate Subtotal & Tax Back-Calculation Split
        # For each item: Taxable Value = Net Price / (1 + (Tax Rate / 100))
        # Tax Amount = Net Price - Taxable Value
        for item in self.cart_items:
            net_item_price = item['price'] * item['qty']
            subtotal += net_item_price
            
            tax_rate = item['tax_rate']
            taxable_value = net_item_price / (1.0 + (tax_rate / 100.0))
            tax_amt = net_item_price - taxable_value
            total_tax_pool += tax_amt

        # Discount parse
        discount = 0.0
        disc_str = self.ent_discount.get().strip()
        if disc_str:
            try:
                discount = float(disc_str)
            except ValueError:
                discount = 0.0
                
        # Grand Total calculation (Subtotal - Discount)
        # Note: GST splits must represent exact 50/50 breakdown values of overall tax pool
        cgst_val = total_tax_pool / 2.0
        sgst_val = total_tax_pool / 2.0
        grand_total = max(0.0, subtotal - discount)
        
        # Write formatted values to UI
        self.lbl_subtotal.configure(text=f"₹{subtotal:.2f}")
        self.lbl_cgst.configure(text=f"₹{cgst_val:.2f}")
        self.lbl_sgst.configure(text=f"₹{sgst_val:.2f}")
        self.lbl_grand_total.configure(text=f"₹{grand_total:.2f}")

    def clear_cart_session(self):
        """Resets the billing desk session and fields."""
        self.cart_items = []
        self.ent_discount.delete(0, tk.END)
        self.ent_discount.insert(0, "0")
        self.billing_search_entry.delete(0, tk.END)
        self.refresh_cart_grid()
        self.update_calculations()
        self.hide_billing_search_listbox()
        self.billing_search_entry.focus()
        self.show_status_message("Billing desk session cleared.")

    def trigger_print_routine(self):
        """Triggers the final transactional save and formats printing output."""
        if not self.cart_items:
            self.show_status_message("Cart is empty! Cannot print.", "red")
            return
            
        # 1. Fetch calculations metrics
        subtotal = 0.0
        total_tax_pool = 0.0
        for item in self.cart_items:
            net_item_price = item['price'] * item['qty']
            subtotal += net_item_price
            taxable_val = net_item_price / (1.0 + (item['tax_rate'] / 100.0))
            total_tax_pool += (net_item_price - taxable_val)
            
        discount = 0.0
        try:
            discount = float(self.ent_discount.get().strip())
        except ValueError:
            discount = 0.0
            
        cgst = total_tax_pool / 2.0
        sgst = total_tax_pool / 2.0
        grand_total = max(0.0, subtotal - discount)
        
        # 2. Persist invoice to SQLite ledger
        try:
            invoice_id = database.save_invoice(subtotal, discount, total_tax_pool, grand_total, self.cart_items)
            if not invoice_id:
                self.show_status_message("Ledger Save Failed!", "red")
                return
        except Exception as e:
            self.show_status_message(f"Ledger Write Crash: {e}", "red")
            return

        # 3. Compile monospace text matching the 80mm format guidelines
        shop_config = database.get_shop_config()
        receipt_buffer = printer.generate_receipt_string(
            shop_config,
            invoice_id,
            self.cart_items,
            subtotal,
            discount,
            cgst,
            sgst,
            grand_total
        )
        
        # 4. Spool to default printer device/file
        try:
            success, destination = printer.send_to_printer(receipt_buffer)
            if success:
                self.show_status_message(f"Printed via {destination} successfully!")
                self.clear_cart_session()
                # Refresh inventory grid in case quantities updated
                self.refresh_inventory_grid()
            else:
                self.show_status_message(f"Print Fail: {destination}", "red")
        except Exception as e:
            self.show_status_message(f"Hardware spool error: {e}", "red")

    # =========================================================================
    # 📦 INVENTORY MASTER MODULE RUNTIME LOGIC
    # =========================================================================
    def refresh_inventory_grid(self, search_query=""):
        """Loads and updates products in the database list Treeview."""
        # Clear Treeview
        for r in self.inv_tree.get_children():
            self.inv_tree.delete(r)
            
        try:
            if search_query:
                products = database.search_products(search_query)
            else:
                products = database.get_all_products()
                
            for p in products:
                self.inv_tree.insert(
                    "",
                    "end",
                    values=(p['id'], p['name'], f"{p['price']:.2f}", f"{p['tax_rate']}%")
                )
        except Exception as e:
            self.show_status_message(f"Failed to fetch products: {e}", "red", "inventory")

    def refresh_billing_catalog_items(self):
        """Pre-loads/caches catalog arrays to ensure zero latency during searches."""
        # Search query automatically fetches from SQLite in real-time.
        pass

    def on_inventory_save_click(self):
        """Processes add or edit save requests for product settings."""
        name = self.ent_prod_name.get().strip()
        price_str = self.ent_prod_price.get().strip()
        tax_str = self.cmb_prod_tax.get().strip()
        
        if not name or not price_str or not tax_str:
            self.show_status_message("Please fill all product fields!", "red", "inventory")
            return
            
        try:
            price = float(price_str)
            tax_rate = float(tax_str)
        except ValueError:
            self.show_status_message("MRP must be a valid number!", "red", "inventory")
            return
            
        if self.current_selected_prod_id:
            # Edit mode active
            try:
                success = database.update_product(self.current_selected_prod_id, name, price, tax_rate)
                if success:
                    self.show_status_message("Product updated successfully!", "green", "inventory")
                    self.exit_inventory_edit_mode()
                    self.refresh_inventory_grid()
                else:
                    self.show_status_message("Product name must be unique!", "red", "inventory")
            except Exception as e:
                self.show_status_message(f"Edit failed: {e}", "red", "inventory")
        else:
            # Add mode active
            try:
                product_id = database.add_product(name, price, tax_rate)
                if product_id > 0:
                    self.show_status_message("Product registered in database!", "green", "inventory")
                    self.clear_inventory_form_inputs()
                    self.refresh_inventory_grid()
                elif product_id == -1:
                    self.show_status_message("Product name already exists!", "red", "inventory")
                else:
                    self.show_status_message("Database register failed.", "red", "inventory")
            except Exception as e:
                self.show_status_message(f"Add failed: {e}", "red", "inventory")

    def on_inventory_edit_click(self):
        """Loads selected Treeview product into input fields for update editing."""
        selected = self.inv_tree.selection()
        if not selected:
            self.show_status_message("Select an item to edit!", "red", "inventory")
            return
            
        row_values = self.inv_tree.item(selected[0])['values']
        self.current_selected_prod_id = int(row_values[0])
        
        # Populate inputs
        self.ent_prod_name.delete(0, tk.END)
        self.ent_prod_name.insert(0, row_values[1])
        
        self.ent_prod_price.delete(0, tk.END)
        self.ent_prod_price.insert(0, str(row_values[2]))
        
        tax_pct = str(row_values[3]).replace("%", "")
        self.cmb_prod_tax.set(tax_pct)
        
        # Toggle buttons
        self.lbl_inv_form_title.configure(text="✏️ EDIT SELECTED PRODUCT", text_color="#00d2ff")
        self.btn_cancel_prod_edit.grid()
        self.btn_save_prod.configure(text="💾 Update Product", fg_color="#00d2ff", text_color="#080c14", hover_color="#00b4db")

    def exit_inventory_edit_mode(self):
        """Cancels product edit mode and returns form state to standard Add Product."""
        self.current_selected_prod_id = None
        self.clear_inventory_form_inputs()
        self.lbl_inv_form_title.configure(text="📦 ADD PRODUCT DATABASE", text_color="#00d2ff")
        self.btn_cancel_prod_edit.grid_remove()
        self.btn_save_prod.configure(text="💾 Save Product", fg_color="#38b000", text_color="#f8f9fa", hover_color="#2c8f00")

    def clear_inventory_form_inputs(self):
        """Resets the inventory form fields."""
        self.ent_prod_name.delete(0, tk.END)
        self.ent_prod_price.delete(0, tk.END)
        self.cmb_prod_tax.set("18.0")

    def on_inventory_delete_click(self):
        """Deletes the highlighted product from the sqlite database."""
        selected = self.inv_tree.selection()
        if not selected:
            self.show_status_message("Select an item to delete!", "red", "inventory")
            return
            
        row_values = self.inv_tree.item(selected[0])['values']
        prod_id = int(row_values[0])
        prod_name = row_values[1]
        
        # Confirm delete action
        if tk.messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{prod_name}' from inventory?"):
            try:
                if database.delete_product(prod_id):
                    self.show_status_message(f"Product '{prod_name}' removed.", "green", "inventory")
                    self.refresh_inventory_grid()
                    # Exit edit mode if the deleted item was being edited
                    if self.current_selected_prod_id == prod_id:
                        self.exit_inventory_edit_mode()
                else:
                    self.show_status_message("Delete operation failed in DB.", "red", "inventory")
            except Exception as e:
                self.show_status_message(f"Delete Failed: {e}", "red", "inventory")

    # =========================================================================
    # ⚙️ SHOP SETTINGS CONFIGURATION RUNTIME LOGIC
    # =========================================================================
    def load_shop_config_to_ui(self):
        """Fetches settings from SQLite database and writes them to UI inputs."""
        try:
            config = database.get_shop_config()
            if config:
                self.ent_shop_name.delete(0, tk.END)
                self.ent_shop_name.insert(0, config['name'])
                
                self.ent_shop_addr1.delete(0, tk.END)
                self.ent_shop_addr1.insert(0, config['address1'])
                
                self.ent_shop_addr2.delete(0, tk.END)
                self.ent_shop_addr2.insert(0, config['address2'])
                
                self.ent_shop_phone.delete(0, tk.END)
                self.ent_shop_phone.insert(0, config['phone'])
                
                self.ent_shop_gstin.delete(0, tk.END)
                self.ent_shop_gstin.insert(0, config['gstin'])
        except Exception as e:
            self.show_status_message(f"Load settings error: {e}", "red", "settings")

    def on_shop_config_save_click(self):
        """Saves current Shop Settings entries to the SQLite database."""
        name = self.ent_shop_name.get().strip()
        addr1 = self.ent_shop_addr1.get().strip()
        addr2 = self.ent_shop_addr2.get().strip()
        phone = self.ent_shop_phone.get().strip()
        gstin = self.ent_shop_gstin.get().strip()
        
        if not name or not addr1:
            self.show_status_message("Name and Address Line 1 are required!", "red", "settings")
            return
            
        try:
            success = database.save_shop_config(name, addr1, addr2, phone, gstin)
            if success:
                self.show_status_message("Configuration saved successfully!", "green", "settings")
            else:
                self.show_status_message("Persistence error. Check terminal logs.", "red", "settings")
        except Exception as e:
            self.show_status_message(f"Settings Save Crash: {e}", "red", "settings")


if __name__ == "__main__":
    # Initialize app window thread loop
    app = POSApp()
    app.mainloop()
