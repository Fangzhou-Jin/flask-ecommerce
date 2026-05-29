/**
 * API client: fetch wrapper with automatic JWT attachment.
 */

const API = {
  getToken() {
    return localStorage.getItem("access_token");
  },

  setToken(token) {
    if (token) {
      localStorage.setItem("access_token", token);
    } else {
      localStorage.removeItem("access_token");
    }
  },

  setUser(user) {
    if (user) {
      localStorage.setItem("user", JSON.stringify(user));
    } else {
      localStorage.removeItem("user");
    }
  },

  getUser() {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  },

  async request(path, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(path, {
      ...options,
      headers,
    });

    let data = null;
    const text = await response.text();
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = { message: text };
      }
    }

    if (!response.ok) {
      const message = data?.message || `Request failed (${response.status})`;
      const error = new Error(message);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  },

  register(username, password, role) {
    return this.request("/register", {
      method: "POST",
      body: JSON.stringify({ username, password, role }),
    });
  },

  login(username, password) {
    return this.request("/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  },

  getStores() {
    return this.request("/stores");
  },

  getMyStore() {
    return this.request("/stores/mine");
  },

  createStore(name) {
    return this.request("/stores", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  },

  updateStore(id, name) {
    return this.request(`/stores/${id}`, {
      method: "PUT",
      body: JSON.stringify({ name }),
    });
  },

  deleteStore(id) {
    return this.request(`/stores/${id}`, { method: "DELETE" });
  },

  getItems() {
    return this.request("/items");
  },

  getMyItems() {
    return this.request("/items/mine");
  },

  createItem(payload) {
    return this.request("/items", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateItem(id, payload) {
    return this.request(`/items/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteItem(id) {
    return this.request(`/items/${id}`, { method: "DELETE" });
  },

  getTags() {
    return this.request("/tags");
  },

  createTag(name) {
    return this.request("/tags", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  },

  linkTagToItem(itemId, tagId) {
    return this.request(`/items/${itemId}/tags/${tagId}`, {
      method: "POST",
    });
  },

  getCart() {
    return this.request("/cart");
  },

  addToCart(itemId, quantity = 1) {
    return this.request("/cart/items", {
      method: "POST",
      body: JSON.stringify({ item_id: itemId, quantity }),
    });
  },

  updateCartItem(itemId, quantity) {
    return this.request(`/cart/items/${itemId}`, {
      method: "PUT",
      body: JSON.stringify({ quantity }),
    });
  },

  removeFromCart(itemId) {
    return this.request(`/cart/items/${itemId}`, { method: "DELETE" });
  },

  clearCart() {
    return this.request("/cart", { method: "DELETE" });
  },
};
