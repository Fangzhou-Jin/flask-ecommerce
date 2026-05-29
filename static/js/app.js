/**
 * Frontend logic: panel switching, CRUD operations, JWT state, dashboard.
 */

const ROLES = {
  MERCHANT: "merchant",
  CUSTOMER: "customer",
};

const TITLES = {
  dashboard: "Overview",
  auth: "Login / Register",
  stores: "My Store",
  items: "Items",
  cart: "Cart",
  tags: "Tag Management",
};

const SUBTITLES = {
  dashboard: "System summary and quick actions",
  auth: "Choose account type and sign in",
  stores: "Merchants only: create and manage your store",
  items: "Browse items or manage your store products",
  cart: "Customers only: view and manage selected items",
  tags: "Merchants only: tag categories and item links",
};

let storesCache = [];
let itemsCache = [];
let tagsCache = [];
let cartCache = null;

let storeSearchQuery = "";
let itemSearchQuery = "";
let itemFilterStoreId = "";
let tagSearchQuery = "";

function showToast(message, type = "info") {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.className = `toast ${type}`;
  el.classList.remove("hidden");
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => el.classList.add("hidden"), 3500);
}

function isLoggedIn() {
  return !!API.getToken();
}

function getUserRole() {
  return API.getUser()?.role;
}

function isMerchant() {
  return getUserRole() === ROLES.MERCHANT;
}

function isCustomer() {
  return getUserRole() === ROLES.CUSTOMER;
}

function canManageStores() {
  return isLoggedIn() && isMerchant();
}

function canManageItems() {
  return isLoggedIn() && isMerchant();
}

function canUseCart() {
  return isLoggedIn() && isCustomer();
}

function setLoading(id, loading) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle("hidden", !loading);
}

function updateNavBadges() {
  document.getElementById("nav-badge-stores").textContent = storesCache.length;
  document.getElementById("nav-badge-items").textContent = itemsCache.length;
  document.getElementById("nav-badge-tags").textContent = tagsCache.length;
  const cartQty = cartCache?.total_quantity ?? 0;
  const cartBadge = document.getElementById("nav-badge-cart");
  cartBadge.textContent = cartQty;
  cartBadge.classList.toggle("has-items", cartQty > 0);
}

async function updateCartBadge() {
  if (!canUseCart()) {
    cartCache = null;
    updateNavBadges();
    return;
  }
  try {
    cartCache = await API.getCart();
    updateNavBadges();
  } catch {
    cartCache = null;
  }
}

function applyRoleUI() {
  const loggedIn = isLoggedIn();
  const role = getUserRole();

  document.querySelectorAll(".nav-btn[data-role]").forEach((btn) => {
    btn.classList.toggle("hidden", !loggedIn || role !== btn.dataset.role);
  });

  document.querySelectorAll(".quick-btn[data-role]").forEach((btn) => {
    btn.classList.toggle("hidden", !loggedIn || role !== btn.dataset.role);
  });

  const itemsLabel = document.getElementById("nav-label-items");
  const quickItemsLabel = document.getElementById("quick-label-items");
  const itemsTitle = loggedIn && isMerchant() ? "My Items" : "Browse Items";
  if (itemsLabel) itemsLabel.textContent = itemsTitle;
  if (quickItemsLabel) quickItemsLabel.textContent = loggedIn && isMerchant() ? "My Items" : "Browse Items";

  document.getElementById("items-intro-customer")?.classList.toggle("hidden", loggedIn && isMerchant());
  document.getElementById("items-intro-merchant")?.classList.toggle("hidden", !loggedIn || !isMerchant());
  document.getElementById("item-form-card")?.classList.toggle("hidden", !canManageItems());
  document.getElementById("item-filter-store")?.classList.toggle("hidden", loggedIn && isMerchant());

  const roleLabels = { merchant: "Merchant", customer: "Customer" };
  const roleEl = document.querySelector(".user-role");
  if (roleEl) {
    roleEl.textContent = loggedIn ? roleLabels[role] || "Signed in" : "";
  }

  ["store-submit", "item-submit", "tag-submit", "link-submit"].forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (id === "store-submit") el.disabled = !canManageStores();
    else if (id === "item-submit") el.disabled = !canManageItems();
    else el.disabled = !canManageItems();
  });
}

function updateAuthUI() {
  const loggedIn = isLoggedIn();
  const user = API.getUser();

  document.getElementById("logout-btn").classList.toggle("hidden", !loggedIn);
  document.getElementById("user-badge").classList.toggle("hidden", !loggedIn);

  if (loggedIn && user) {
    document.getElementById("username-display").textContent = user.username;
    document.getElementById("user-avatar").textContent = user.username.charAt(0).toUpperCase();
  }

  applyRoleUI();
  updateCartBadge();
  if (!loggedIn) cartCache = null;
  updateNavBadges();
}

function switchPanel(name) {
  const role = getUserRole();
  if (name === "cart" && role === ROLES.MERCHANT) {
    showToast("Merchant accounts cannot use the cart", "error");
    return;
  }
  if ((name === "stores" || name === "tags") && isLoggedIn() && role === ROLES.CUSTOMER) {
    showToast("Customer accounts cannot access this section", "error");
    return;
  }

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.panel === name);
  });
  document.querySelectorAll(".panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `panel-${name}`);
  });
  document.getElementById("page-title").textContent = TITLES[name] || name;
  document.getElementById("page-subtitle").textContent = SUBTITLES[name] || "";

  if (name === "dashboard") loadDashboard();
  if (name === "stores") loadStores();
  if (name === "items") loadItems();
  if (name === "cart") loadCart();
  if (name === "tags") loadTags();
}

/* ---- Modal ---- */

const modal = document.getElementById("modal");
const modalForm = document.getElementById("modal-form");
let modalCallback = null;

function openModal(title, fields, onSubmit) {
  document.getElementById("modal-title").textContent = title;
  modalForm.innerHTML = fields
    .map((f) => {
      if (f.type === "select") {
        const opts = f.options
          .map((o) => `<option value="${o.value}" ${o.value == f.value ? "selected" : ""}>${escapeHtml(o.label)}</option>`)
          .join("");
        return `<label><span class="label-text">${f.label}</span><select name="${f.name}" required>${opts}</select></label>`;
      }
      return `<label><span class="label-text">${f.label}</span><input type="${f.type || "text"}" name="${f.name}" value="${f.value ?? ""}" ${f.attrs || ""} required /></label>`;
    })
    .join("");
  modalCallback = onSubmit;
  modal.classList.remove("hidden");
}

function closeModal() {
  modal.classList.add("hidden");
  modalCallback = null;
}

/* ---- Confirm modal ---- */

const confirmModal = document.getElementById("confirm-modal");
let confirmCallback = null;

function openConfirm(title, message, onConfirm) {
  document.getElementById("confirm-title").textContent = title;
  document.getElementById("confirm-message").textContent = message;
  confirmCallback = onConfirm;
  confirmModal.classList.remove("hidden");
}

function closeConfirm() {
  confirmModal.classList.add("hidden");
  confirmCallback = null;
}

document.getElementById("confirm-cancel").addEventListener("click", closeConfirm);
document.getElementById("confirm-ok").addEventListener("click", async () => {
  if (confirmCallback) await confirmCallback();
  closeConfirm();
});
document.querySelector("#confirm-modal .modal-backdrop").addEventListener("click", closeConfirm);

document.getElementById("modal-cancel").addEventListener("click", closeModal);
document.querySelector("#modal .modal-backdrop").addEventListener("click", closeModal);

modalForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData(modalForm);
  const data = Object.fromEntries(formData.entries());
  if (modalCallback) await modalCallback(data);
});

/* ---- Password toggle ---- */

document.querySelectorAll(".toggle-pwd").forEach((btn) => {
  btn.addEventListener("click", () => {
    const input = btn.previousElementSibling;
    const isPassword = input.type === "password";
    input.type = isPassword ? "text" : "password";
    btn.textContent = isPassword ? "🙈" : "👁";
  });
});

/* ---- Auth ---- */

document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    const result = await API.login(fd.get("username"), fd.get("password"));
    API.setToken(result.access_token);
    API.setUser(result.user);
    updateAuthUI();
    showToast(`Welcome back, ${result.user.username}!`, "success");
    e.target.reset();
    await updateCartBadge();
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await API.register(fd.get("username"), fd.get("password"), fd.get("role"));
    showToast("Registration successful. Please sign in.", "success");
    e.target.reset();
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("logout-btn").addEventListener("click", () => {
  API.setToken(null);
  API.setUser(null);
  updateAuthUI();
  showToast("Logged out", "info");
  switchPanel("auth");
});

/* ---- Dashboard ---- */

function countItemsByStore(storeId) {
  return itemsCache.filter((i) => i.store_id === storeId).length;
}

function countItemsByTag(tagId) {
  return itemsCache.filter((i) => (i.tags || []).some((t) => t.id === tagId)).length;
}

function renderDashboard() {
  const storeCount = storesCache.length;
  const itemCount = itemsCache.length;
  const tagCount = tagsCache.length;
  const avgPrice = itemCount
    ? itemsCache.reduce((sum, i) => sum + Number(i.price), 0) / itemCount
    : 0;

  document.getElementById("stat-stores").textContent = storeCount;
  document.getElementById("stat-items").textContent = itemCount;
  document.getElementById("stat-tags").textContent = tagCount;
  document.getElementById("stat-avg-price").textContent = itemCount ? `$${avgPrice.toFixed(2)}` : "—";

  const recentList = document.getElementById("recent-items-list");
  if (!itemsCache.length) {
    recentList.innerHTML = `<li class="recent-empty">No items yet</li>`;
  } else {
    const recent = [...itemsCache].slice(-5).reverse();
    recentList.innerHTML = recent
      .map(
        (item) =>
          `<li><span class="item-name">${escapeHtml(item.name)}</span><span class="item-price">$${Number(item.price).toFixed(2)}</span></li>`
      )
      .join("");
  }

  const distEl = document.getElementById("store-distribution");
  if (!storesCache.length) {
    distEl.innerHTML = `<p class="hint">No store data yet</p>`;
    return;
  }

  const maxCount = Math.max(...storesCache.map((s) => countItemsByStore(s.id)), 1);
  distEl.innerHTML = storesCache
    .map((s) => {
      const count = countItemsByStore(s.id);
      const pct = (count / maxCount) * 100;
      return `
        <div class="dist-row">
          <span class="dist-name" title="${escapeHtml(s.name)}">${escapeHtml(s.name)}</span>
          <div class="dist-bar-wrap"><div class="dist-bar" style="width:${pct}%"></div></div>
          <span class="dist-count">${count} items</span>
        </div>`;
    })
    .join("");

  updateNavBadges();
}

async function loadDashboard() {
  try {
    if (!storesCache.length) storesCache = await API.getStores();
    if (!itemsCache.length) itemsCache = await API.getItems();
    if (!tagsCache.length) tagsCache = await API.getTags();
    renderDashboard();
  } catch (err) {
    showToast(err.message, "error");
  }
}

document.getElementById("refresh-dashboard").addEventListener("click", async () => {
  storesCache = await API.getStores();
  itemsCache = await API.getItems();
  tagsCache = await API.getTags();
  renderDashboard();
  showToast("Data refreshed", "success");
});

document.querySelectorAll(".quick-btn").forEach((btn) => {
  btn.addEventListener("click", () => switchPanel(btn.dataset.goto));
});

document.addEventListener("click", (e) => {
  const goto = e.target.closest("[data-goto]:not(.quick-btn)");
  if (goto) switchPanel(goto.dataset.goto);
});

/* ---- Stores ---- */

function getFilteredStores() {
  if (!storeSearchQuery) return storesCache;
  const q = storeSearchQuery.toLowerCase();
  return storesCache.filter((s) => s.name.toLowerCase().includes(q));
}

function renderStores() {
  const filtered = getFilteredStores();
  const tbody = document.getElementById("stores-tbody");
  document.getElementById("stores-count").textContent = `${filtered.length} result(s)`;

  document.getElementById("store-form-card")?.classList.toggle(
    "hidden",
    canManageStores() && storesCache.length > 0
  );

  if (!filtered.length) {
    const emptyMsg = canManageStores()
      ? "You don't have a store yet — create one first"
      : storeSearchQuery
        ? "No matching stores"
        : "No stores yet";
    tbody.innerHTML = `<tr class="empty-row"><td colspan="4"><div class="empty-state"><span class="empty-icon">🏪</span><span>${emptyMsg}</span></div></td></tr>`;
    updateNavBadges();
    return;
  }

  tbody.innerHTML = filtered
    .map((s) => {
      const itemCount = countItemsByStore(s.id);
      const canEdit = canManageStores() && s.owner_id === API.getUser()?.id;
      return `
    <tr>
      <td class="col-id">${s.id}</td>
      <td><strong>${escapeHtml(s.name)}</strong></td>
      <td class="col-num"><span class="count-badge">${itemCount}</span></td>
      <td>
        <button class="btn btn-edit" data-edit-store="${s.id}" ${canEdit ? "" : "disabled"}>Edit</button>
        <button class="btn btn-danger" data-del-store="${s.id}" ${canEdit ? "" : "disabled"}>Delete</button>
      </td>
    </tr>`;
    })
    .join("");

  updateNavBadges();
}

async function loadStores() {
  setLoading("stores-loading", true);
  try {
    if (canManageStores()) {
      try {
        const myStore = await API.getMyStore();
        storesCache = [myStore];
      } catch (err) {
        if (err.status === 404) {
          storesCache = [];
        } else {
          throw err;
        }
      }
    } else {
      storesCache = await API.getStores();
    }
    if (!itemsCache.length) itemsCache = await API.getItems();
    renderStores();
    refreshStoreSelects();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    setLoading("stores-loading", false);
  }
}

document.getElementById("store-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = new FormData(e.target).get("name");
  try {
    await API.createStore(name);
    e.target.reset();
    showToast("Store created", "success");
    await loadStores();
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("refresh-stores").addEventListener("click", loadStores);

document.getElementById("store-search").addEventListener("input", (e) => {
  storeSearchQuery = e.target.value.trim();
  renderStores();
});

document.getElementById("stores-tbody").addEventListener("click", async (e) => {
  const editId = e.target.dataset.editStore;
  const delId = e.target.dataset.delStore;

  if (editId) {
    const store = storesCache.find((s) => s.id === Number(editId));
    openModal("Edit Store", [{ label: "Store name", name: "name", value: store.name }], async (data) => {
      try {
        await API.updateStore(editId, data.name);
        closeModal();
        showToast("Store updated", "success");
        await loadStores();
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  }

  if (delId) {
    const store = storesCache.find((s) => s.id === Number(delId));
    const itemCount = countItemsByStore(store.id);
    openConfirm(
      "Delete Store",
      `Delete "${store.name}"?${itemCount ? ` This will also remove ${itemCount} item(s) in the store.` : ""}`,
      async () => {
        try {
          await API.deleteStore(delId);
          showToast("Store deleted", "success");
          itemsCache = [];
          await loadStores();
        } catch (err) {
          showToast(err.message, "error");
        }
      }
    );
  }
});

function refreshStoreSelects() {
  const merchantStore = canManageItems() && storesCache.length ? storesCache : [];
  const catalogStores = storesCache;

  const options =
    `<option value="">Select store</option>` +
    catalogStores.map((s) => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join("");

  const itemStoreSelect = document.getElementById("item-store-select");
  if (canManageItems() && merchantStore.length) {
    itemStoreSelect.innerHTML = merchantStore
      .map((s) => `<option value="${s.id}" selected>${escapeHtml(s.name)}</option>`)
      .join("");
    itemStoreSelect.disabled = true;
  } else {
    itemStoreSelect.innerHTML = options;
    itemStoreSelect.disabled = false;
  }

  const filterSelect = document.getElementById("item-filter-store");
  const current = filterSelect.value;
  filterSelect.innerHTML =
    `<option value="">All stores</option>` +
    catalogStores.map((s) => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join("");
  filterSelect.value = current;
}

/* ---- Items ---- */

function getFilteredItems() {
  let list = itemsCache;
  if (itemFilterStoreId) {
    list = list.filter((i) => i.store_id === Number(itemFilterStoreId));
  }
  if (itemSearchQuery) {
    const q = itemSearchQuery.toLowerCase();
    list = list.filter((i) => i.name.toLowerCase().includes(q));
  }
  return list;
}

function renderItems() {
  const filtered = getFilteredItems();
  const tbody = document.getElementById("items-tbody");
  document.getElementById("items-count").textContent = `${filtered.length} result(s)`;

  if (!filtered.length) {
    const emptyMsg =
      itemSearchQuery || itemFilterStoreId
        ? "No matching items"
        : canManageItems()
          ? "No items in your store yet — add one"
          : "No items yet";
    tbody.innerHTML = `<tr class="empty-row"><td colspan="6"><div class="empty-state"><span class="empty-icon">📦</span><span>${emptyMsg}</span></div></td></tr>`;
    return;
  }

  tbody.innerHTML = filtered
    .map((item) => {
      const store = storesCache.find((s) => s.id === item.store_id);
      const tags = (item.tags || [])
        .map((t) => `<span class="tag-pill">${escapeHtml(t.name)}</span>`)
        .join("");

      let actions = "";
      if (canUseCart()) {
        actions += `<button class="btn btn-cart" data-add-cart="${item.id}" title="Add to cart">🛒</button>`;
      }
      if (canManageItems()) {
        actions += `<button class="btn btn-edit" data-edit-item="${item.id}">Edit</button>`;
        actions += `<button class="btn btn-danger" data-del-item="${item.id}">Delete</button>`;
      }
      if (!actions) {
        actions = '<span style="color:var(--muted)">—</span>';
      }

      return `
    <tr>
      <td class="col-id">${item.id}</td>
      <td><strong>${escapeHtml(item.name)}</strong></td>
      <td class="price-cell">$${Number(item.price).toFixed(2)}</td>
      <td>${store ? `<span class="store-chip">${escapeHtml(store.name)}</span>` : item.store_id}</td>
      <td>${tags || '<span style="color:var(--muted)">—</span>'}</td>
      <td>${actions}</td>
    </tr>`;
    })
    .join("");

  updateNavBadges();
}

async function loadItems() {
  setLoading("items-loading", true);
  try {
    if (canManageItems()) {
      try {
        const myStore = await API.getMyStore();
        storesCache = [myStore];
      } catch (err) {
        if (err.status !== 404) throw err;
        storesCache = [];
      }
      itemsCache = await API.getMyItems();
    } else {
      if (!storesCache.length) storesCache = await API.getStores();
      itemsCache = await API.getItems();
    }
    renderItems();
    refreshStoreSelects();
    refreshLinkSelects();
    applyRoleUI();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    setLoading("items-loading", false);
  }
}

document.getElementById("item-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const storeId = canManageItems()
    ? storesCache[0]?.id
    : parseInt(fd.get("store_id"), 10);

  if (!storeId) {
    showToast("Create a store before adding items", "error");
    return;
  }

  try {
    await API.createItem({
      name: fd.get("name"),
      price: parseFloat(fd.get("price")),
      store_id: storeId,
    });
    e.target.reset();
    showToast("Item created", "success");
    await loadItems();
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("refresh-items").addEventListener("click", loadItems);

document.getElementById("item-search").addEventListener("input", (e) => {
  itemSearchQuery = e.target.value.trim();
  renderItems();
});

document.getElementById("item-filter-store").addEventListener("change", (e) => {
  itemFilterStoreId = e.target.value;
  renderItems();
});

document.getElementById("items-tbody").addEventListener("click", async (e) => {
  const addId = e.target.dataset.addCart;
  const editId = e.target.dataset.editItem;
  const delId = e.target.dataset.delItem;

  if (addId) {
    try {
      cartCache = await API.addToCart(addId, 1);
      updateNavBadges();
      showToast("Added to cart", "success");
    } catch (err) {
      showToast(err.message, "error");
    }
    return;
  }

  if (editId) {
    const item = itemsCache.find((i) => i.id === Number(editId));
    openModal(
      "Edit Item",
      [
        { label: "Item name", name: "name", value: item.name },
        { label: "Price ($)", name: "price", type: "number", value: item.price, attrs: 'step="0.01" min="0"' },
        {
          label: "Store",
          name: "store_id",
          type: "select",
          value: item.store_id,
          options: storesCache.map((s) => ({ value: s.id, label: s.name })),
        },
      ],
      async (data) => {
        try {
          await API.updateItem(editId, {
            name: data.name,
            price: parseFloat(data.price),
            store_id: parseInt(data.store_id, 10),
          });
          closeModal();
          showToast("Item updated", "success");
          await loadItems();
        } catch (err) {
          showToast(err.message, "error");
        }
      }
    );
  }

  if (delId) {
    const item = itemsCache.find((i) => i.id === Number(delId));
    openConfirm("Delete Item", `Delete "${item.name}"? This cannot be undone.`, async () => {
      try {
        await API.deleteItem(delId);
        showToast("Item deleted", "success");
        await loadItems();
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  }
});

function refreshLinkSelects() {
  const itemSelect = document.getElementById("link-item-select");
  itemSelect.innerHTML =
    `<option value="">Select item</option>` +
    itemsCache.map((i) => `<option value="${i.id}">${escapeHtml(i.name)}</option>`).join("");

  const tagSelect = document.getElementById("link-tag-select");
  tagSelect.innerHTML =
    `<option value="">Select tag</option>` +
    tagsCache.map((t) => `<option value="${t.id}">${escapeHtml(t.name)}</option>`).join("");
}

/* ---- Cart ---- */

function renderCart() {
  const loggedIn = isLoggedIn();
  const isCustomerUser = canUseCart();

  document.getElementById("cart-login-hint").classList.toggle("hidden", isCustomerUser);
  document.getElementById("cart-content").classList.toggle("hidden", !isCustomerUser);
  document.getElementById("cart-intro").classList.toggle("hidden", !loggedIn || !isCustomerUser);

  if (!isCustomerUser || !cartCache) {
    const hintMsg = document.getElementById("cart-hint-message");
    const hintAction = document.getElementById("cart-hint-action");
    if (loggedIn && isMerchant()) {
      document.getElementById("cart-login-hint").classList.remove("hidden");
      if (hintMsg) hintMsg.textContent = "Merchant accounts cannot use the cart. Please sign in as a customer.";
      hintAction?.classList.add("hidden");
    } else if (!loggedIn) {
      document.getElementById("cart-login-hint").classList.remove("hidden");
      if (hintMsg) hintMsg.textContent = "Please sign in to use the cart";
      hintAction?.classList.remove("hidden");
    }
    return;
  }

  const lines = cartCache.items || [];
  const tbody = document.getElementById("cart-tbody");

  document.getElementById("cart-kind-count").textContent = lines.length;
  document.getElementById("cart-total-qty").textContent = cartCache.total_quantity;
  document.getElementById("cart-total-price").textContent = `$${Number(cartCache.total_price).toFixed(2)}`;
  document.getElementById("cart-count").textContent = `${lines.length} unique item(s)`;

  if (!lines.length) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="5"><div class="empty-state"><span class="empty-icon">🛍️</span><span>Your cart is empty — browse items to get started</span><button class="btn btn-primary btn-sm" data-goto="items">Browse Items</button></div></td></tr>`;
    return;
  }

  tbody.innerHTML = lines
    .map((line) => {
      const item = line.item || {};
      const store = storesCache.find((s) => s.id === item.store_id);
      return `
    <tr>
      <td>
        <div class="cart-item-name">${escapeHtml(item.name || "—")}</div>
        ${store ? `<span class="store-chip">${escapeHtml(store.name)}</span>` : ""}
      </td>
      <td class="price-cell">$${Number(item.price || 0).toFixed(2)}</td>
      <td class="col-qty">
        <div class="qty-control">
          <button class="qty-btn" data-cart-dec="${line.item_id}" ${line.quantity <= 1 ? "disabled" : ""}>−</button>
          <span class="qty-value">${line.quantity}</span>
          <button class="qty-btn" data-cart-inc="${line.item_id}">+</button>
        </div>
      </td>
      <td class="price-cell">$${Number(line.subtotal).toFixed(2)}</td>
      <td>
        <button class="btn btn-danger" data-cart-remove="${line.item_id}">Remove</button>
      </td>
    </tr>`;
    })
    .join("");

  updateNavBadges();
}

async function loadCart() {
  if (!canUseCart()) {
    renderCart();
    return;
  }

  setLoading("cart-loading", true);
  try {
    if (!storesCache.length) storesCache = await API.getStores();
    cartCache = await API.getCart();
    renderCart();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    setLoading("cart-loading", false);
  }
}

document.getElementById("refresh-cart").addEventListener("click", loadCart);

document.getElementById("clear-cart").addEventListener("click", () => {
  if (!cartCache?.items?.length) {
    showToast("Your cart is already empty", "info");
    return;
  }
  openConfirm("Clear Cart", "Remove all items from your cart?", async () => {
    try {
      cartCache = await API.clearCart();
      renderCart();
      showToast("Cart cleared", "success");
    } catch (err) {
      showToast(err.message, "error");
    }
  });
});

document.getElementById("cart-tbody").addEventListener("click", async (e) => {
  const incId = e.target.dataset.cartInc;
  const decId = e.target.dataset.cartDec;
  const removeId = e.target.dataset.cartRemove;

  if (incId) {
    const line = cartCache.items.find((l) => l.item_id === Number(incId));
    try {
      cartCache = await API.updateCartItem(incId, line.quantity + 1);
      renderCart();
    } catch (err) {
      showToast(err.message, "error");
    }
    return;
  }

  if (decId) {
    const line = cartCache.items.find((l) => l.item_id === Number(decId));
    if (line.quantity <= 1) return;
    try {
      cartCache = await API.updateCartItem(decId, line.quantity - 1);
      renderCart();
    } catch (err) {
      showToast(err.message, "error");
    }
    return;
  }

  if (removeId) {
    const line = cartCache.items.find((l) => l.item_id === Number(removeId));
    openConfirm("Remove Item", `Remove "${line.item?.name}" from your cart?`, async () => {
      try {
        cartCache = await API.removeFromCart(removeId);
        renderCart();
        showToast("Removed from cart", "success");
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  }
});

/* ---- Tags ---- */

function getFilteredTags() {
  if (!tagSearchQuery) return tagsCache;
  const q = tagSearchQuery.toLowerCase();
  return tagsCache.filter((t) => t.name.toLowerCase().includes(q));
}

function renderTags() {
  const filtered = getFilteredTags();
  const tbody = document.getElementById("tags-tbody");
  document.getElementById("tags-count").textContent = `${filtered.length} result(s)`;

  if (!filtered.length) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="3"><div class="empty-state"><span class="empty-icon">🏷️</span><span>${tagSearchQuery ? "No matching tags" : "No tags yet — add one first"}</span></div></td></tr>`;
    return;
  }

  tbody.innerHTML = filtered
    .map((t) => {
      const linked = countItemsByTag(t.id);
      return `
    <tr>
      <td class="col-id">${t.id}</td>
      <td><span class="tag-pill">${escapeHtml(t.name)}</span></td>
      <td class="col-num"><span class="count-badge">${linked}</span></td>
    </tr>`;
    })
    .join("");

  updateNavBadges();
}

async function loadTags() {
  setLoading("tags-loading", true);
  try {
    tagsCache = await API.getTags();
    if (!itemsCache.length) {
      if (!storesCache.length) storesCache = await API.getStores();
      itemsCache = await API.getItems();
    }
    renderTags();
    refreshLinkSelects();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    setLoading("tags-loading", false);
  }
}

document.getElementById("tag-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = new FormData(e.target).get("name");
  try {
    await API.createTag(name);
    e.target.reset();
    showToast("Tag created", "success");
    await loadTags();
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("link-tag-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await API.linkTagToItem(fd.get("item_id"), fd.get("tag_id"));
    showToast("Tag linked successfully", "success");
    await loadItems();
    await loadTags();
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("refresh-tags").addEventListener("click", loadTags);

document.getElementById("tag-search").addEventListener("input", (e) => {
  tagSearchQuery = e.target.value.trim();
  renderTags();
});

/* ---- Navigation ---- */

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => switchPanel(btn.dataset.panel));
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

updateAuthUI();
loadDashboard();
