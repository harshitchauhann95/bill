/**
 * @module InventoryMaster
 * @description Product CRUD engine backed by localStorage.
 * Products are stored as an array of objects for fast cart lookup and barcode scanning.
 */
const InventoryMaster = {
  STORAGE_KEY: 'iot_billing_inventory',

  /** @returns {Array} All products */
  getAll() {
    return JSON.parse(localStorage.getItem(this.STORAGE_KEY) || '[]');
  },

  /** @param {Object} product - { name, price, stock, barcode, category } */
  add(product) {
    const products = this.getAll();
    product.id = Date.now().toString();
    product.createdAt = new Date().toISOString();
    products.push(product);
    this._persist(products);
    document.dispatchEvent(new CustomEvent('inventory:updated'));
    return product;
  },

  /** @param {string} id - Product ID to update */
  update(id, updates) {
    const products = this.getAll().map(p =>
      p.id === id ? { ...p, ...updates, updatedAt: new Date().toISOString() } : p
    );
    this._persist(products);
    document.dispatchEvent(new CustomEvent('inventory:updated'));
  },

  /** @param {string} id - Product ID to remove */
  delete(id) {
    this._persist(this.getAll().filter(p => p.id !== id));
    document.dispatchEvent(new CustomEvent('inventory:updated'));
  },

  /** @param {string} query - Name or barcode search */
  search(query) {
    if (!query) return this.getAll();
    return this.getAll().filter(p =>
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      (p.barcode && p.barcode === query)
    );
  },

  _persist(products) {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(products));
  },
};
