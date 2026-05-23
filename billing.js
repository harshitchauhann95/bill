/**
 * @module BillingDesk
 * @description Core cart engine with GST computation.
 * Handles item addition, quantity management, discount application, and tax calculations.
 */
const BillingDesk = {
  cart: [],
  TAX_RATE: 0.18, // 18% GST

  /** @param {Object} product - Product from InventoryMaster */
  addToCart(product, quantity = 1) {
    const existing = this.cart.find(i => i.id === product.id);
    if (existing) {
      existing.quantity += quantity;
    } else {
      this.cart.push({ ...product, quantity });
    }
    this._dispatchUpdate();
  },

  removeFromCart(productId) {
    this.cart = this.cart.filter(i => i.id !== productId);
    this._dispatchUpdate();
  },

  updateQuantity(productId, quantity) {
    if (quantity <= 0) {
      this.removeFromCart(productId);
      return;
    }
    const item = this.cart.find(i => i.id === productId);
    if (item) {
      item.quantity = quantity;
    }
    this._dispatchUpdate();
  },

  /** @returns {Object} { subtotal, tax, discount, total } */
  computeTotals(discountPercent = 0) {
    const subtotal = this.cart.reduce(
      (sum, item) => sum + item.price * item.quantity, 0
    );
    const discount = subtotal * (discountPercent / 100);
    const taxable  = subtotal - discount;
    const tax      = taxable * this.TAX_RATE;
    const total    = taxable + tax;
    return {
      subtotal:  subtotal.toFixed(2),
      discount:  discount.toFixed(2),
      tax:       tax.toFixed(2),
      total:     total.toFixed(2),
    };
  },

  clearCart() {
    this.cart = [];
    this._dispatchUpdate();
  },

  printBill() {
    window.print();
  },

  _dispatchUpdate() {
    document.dispatchEvent(new CustomEvent('cart:updated', { detail: this.cart }));
  }
};
