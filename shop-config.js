/**
 * @module ShopConfig
 * @description Persistence layer for shop identity.
 * Stores shop name, address, GST number, phone, and currency in localStorage.
 */
const ShopConfig = {
  STORAGE_KEY: 'iot_billing_shop_config',

  save(config) {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(config));
    // Dispatch event to notify UI
    document.dispatchEvent(new CustomEvent('shop-config:updated', { detail: config }));
  },

  load() {
    const raw = localStorage.getItem(this.STORAGE_KEY);
    return raw ? JSON.parse(raw) : this.defaults();
  },

  defaults() {
    return {
      shopName: 'Aether IoT Labs',
      address: '101 Quantum Boulevard, Cyber City',
      gstNumber: '29AAAAA0000A1Z5',
      currency: 'INR',
      phone: '+91 98765 43210',
    };
  },
};
