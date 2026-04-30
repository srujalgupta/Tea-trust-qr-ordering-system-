const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
const pageId = document.body.dataset.page || "";
const cafeName = document.querySelector(".brand strong, .admin-brand strong")?.textContent?.trim() || "Tea Trust Cafe";

function money(value) {
  return `INR ${Number(value || 0).toFixed(2)}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

const FOOD_IMAGE_PALETTES = [
  ["#fff6dc", "#d28b34", "#6f3b18", "#1f7a5c"],
  ["#e8fff2", "#35a96b", "#184d35", "#f6b742"],
  ["#fff0ec", "#ef6f45", "#7b241a", "#2f63f2"],
  ["#eef5ff", "#4e86f7", "#172f62", "#ff9b23"],
  ["#f7f0ff", "#9a62f2", "#341763", "#31a56b"],
  ["#fff8e7", "#f4b247", "#5a3513", "#d94b44"],
];

function paletteForItem(item) {
  const source = `${item.category_name || ""} ${item.name || ""}`.toLowerCase();
  const score = [...source].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return FOOD_IMAGE_PALETTES[score % FOOD_IMAGE_PALETTES.length];
}

function shortFoodLabel(item) {
  const words = String(item.name || "Cafe")
    .replace(/[^\w\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2);
  return (words.join(" ") || "Cafe").slice(0, 20);
}

function generatedFoodArt(item) {
  const [soft, accent, deep, fresh] = paletteForItem(item);
  const label = escapeHtml(shortFoodLabel(item));
  const category = escapeHtml(item.category_name || "Fresh cafe pick");
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="600" height="450" viewBox="0 0 600 450">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="${soft}"/>
          <stop offset="1" stop-color="#ffffff"/>
        </linearGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="20" stdDeviation="18" flood-color="${deep}" flood-opacity=".18"/>
        </filter>
      </defs>
      <rect width="600" height="450" fill="url(#bg)"/>
      <circle cx="500" cy="78" r="118" fill="${accent}" opacity=".16"/>
      <circle cx="96" cy="372" r="142" fill="${fresh}" opacity=".14"/>
      <path d="M0 342 C108 302 170 388 278 344 S463 300 600 348 V450 H0 Z" fill="${deep}" opacity=".07"/>
      <g filter="url(#shadow)">
        <rect x="112" y="116" width="376" height="218" rx="32" fill="#ffffff" opacity=".92"/>
        <circle cx="226" cy="218" r="54" fill="${accent}" opacity=".9"/>
        <path d="M195 224 C219 174 270 174 294 224 C270 207 220 207 195 224 Z" fill="${deep}" opacity=".82"/>
        <path d="M314 199 H394 C413 199 428 214 428 233 C428 252 413 267 394 267 H314 Z" fill="${fresh}" opacity=".88"/>
        <path d="M339 190 C353 169 385 169 399 190" fill="none" stroke="${deep}" stroke-width="12" stroke-linecap="round" opacity=".36"/>
        <text x="300" y="296" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="33" font-weight="800" fill="${deep}">${label}</text>
        <text x="300" y="322" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="700" fill="#65717b">${category}</text>
      </g>
    </svg>
  `;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

const REAL_FOOD_PHOTOS = [
  {
    test: /(tea|chai|tulasi|pudina|elaichi|kesar|darjeeling|green lemon|iced tea)/i,
    url: "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=900&q=80",
  },
  {
    test: /(coffee|bournvita|chocolate|milk|cold coffee|iced coffee)/i,
    url: "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=900&q=80",
  },
  {
    test: /(toast|garlic bread|bread|khari|bun|maska)/i,
    url: "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=900&q=80",
  },
  {
    test: /(sandwich|club|coleslow|chutney|paneer sandwich)/i,
    url: "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=900&q=80",
  },
  {
    test: /(burger)/i,
    url: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=80",
  },
  {
    test: /(fries|wedges|nuggets|crispers|shots|fingers|popcorn|smiles|triangle)/i,
    url: "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?auto=format&fit=crop&w=900&q=80",
  },
  {
    test: /(mocktail|mojito|curacao|pomegranate|green apple)/i,
    url: "https://images.unsplash.com/photo-1536935338788-846bb9981813?auto=format&fit=crop&w=900&q=80",
  },
  {
    test: /(shake|oreo|kit kat|snickers|vanilla|strawberry|banana|lychee|kiwi|guava)/i,
    url: "https://images.unsplash.com/photo-1572490122747-3968b75cc699?auto=format&fit=crop&w=900&q=80",
  },
  {
    test: /(maggi|noodles)/i,
    url: "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=900&q=80",
  },
  {
    test: /(khakhra|bhakhri|thepla)/i,
    url: "https://images.unsplash.com/photo-1624374053855-39a5a1a41402?auto=format&fit=crop&w=900&q=80",
  },
];

function realFoodPhoto(item) {
  const text = `${item.category_name || ""} ${item.name || ""} ${(item.tags || []).join(" ")}`;
  const match = REAL_FOOD_PHOTOS.find((photo) => photo.test.test(text));
  return match?.url || "https://images.unsplash.com/photo-1543352634-a1c51d9f1fa7?auto=format&fit=crop&w=900&q=80";
}

function imageTag(item, className = "") {
  const fallback = generatedFoodArt(item);
  const source = item.image_url || realFoodPhoto(item);
  const classAttribute = className ? ` class="${className}"` : "";
  return `<img${classAttribute} src="${escapeHtml(source)}" data-fallback-src="${escapeHtml(fallback)}" alt="${escapeHtml(item.name)}" loading="lazy">`;
}

function animatePress(element) {
  element.classList.remove("is-pressed");
  void element.offsetWidth;
  element.classList.add("is-pressed");
  window.setTimeout(() => element.classList.remove("is-pressed"), 420);
}

document.addEventListener("error", (event) => {
  const image = event.target;
  if (!(image instanceof HTMLImageElement)) return;
  const fallback = image.dataset.fallbackSrc;
  if (!fallback || image.getAttribute("src") === fallback) return;
  image.classList.add("using-fallback-image");
  image.setAttribute("src", fallback);
}, true);

document.addEventListener("click", (event) => {
  if (!(event.target instanceof Element)) return;
  const animated = event.target.closest(
    ".button, .icon-button, .chip, .customer-action-button, .admin-nav-link, .menu-section-toggle, .stepper button",
  );
  if (animated) animatePress(animated);
});

async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("X-CSRFToken", csrfToken);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
    options.body = JSON.stringify(options.body);
  }
  const response = await fetch(url, {
    credentials: "same-origin",
    ...options,
    headers,
  });
  const contentType = response.headers.get("Content-Type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();
  if (!response.ok) {
    const message = payload?.message || payload || "Request failed.";
    throw new Error(message);
  }
  return payload;
}

function connectSocket() {
  if (!window.io) {
    return null;
  }
  return window.io({ transports: ["websocket", "polling"] });
}

function initCustomerMenu() {
  const hero = document.querySelector(".menu-hero");
  if (!hero) return;

  const tableId = hero.dataset.tableId || null;
  const menuList = document.getElementById("menuList");
  const searchInput = document.getElementById("menuSearch");
  const categoryTabs = document.getElementById("categoryTabs");
  const cartShortcutButton = document.getElementById("cartShortcut");
  const checkoutShortcutButton = document.getElementById("checkoutShortcut");
  const mobileCartShortcutButton = document.getElementById("mobileCartShortcut");
  const mobileCheckoutShortcutButton = document.getElementById("mobileCheckoutShortcut");
  const cartCountEls = [
    document.getElementById("cartItemCount"),
    document.getElementById("mobileCartItemCount"),
  ].filter(Boolean);
  const checkoutAmountEls = [
    document.getElementById("checkoutAmount"),
    document.getElementById("mobileCheckoutAmount"),
  ].filter(Boolean);
  const cartKey = "qrCafeCart";
  const tableKey = "qrCafeTableId";

  let categories = [];
  let items = [];
  let openCategories = new Set();
  let cart = JSON.parse(localStorage.getItem(cartKey) || "{}");

  if (tableId) {
    localStorage.setItem(tableKey, tableId);
  }

  function saveCart() {
    localStorage.setItem(cartKey, JSON.stringify(cart));
  }

  function itemsForCategory(categoryId) {
    const q = searchInput.value.trim().toLowerCase();
    return items.filter((item) => {
      const inCategory = String(item.category_id) === String(categoryId);
      const haystack = `${item.name} ${item.description} ${(item.tags || []).join(" ")}`.toLowerCase();
      return inCategory && (!q || haystack.includes(q));
    });
  }

  function cartStats() {
    return Object.entries(cart).reduce((stats, [id, quantity]) => {
      const item = items.find((candidate) => String(candidate.id) === String(id));
      if (!item || quantity <= 0) return stats;
      stats.count += quantity;
      stats.total += item.price * quantity;
      return stats;
    }, { count: 0, total: 0 });
  }

  function customerPageUrl(path) {
    const url = new URL(path, window.location.origin);
    const savedTableId = tableId || localStorage.getItem(tableKey) || "";
    if (savedTableId) {
      url.searchParams.set("table", savedTableId);
    }
    return `${url.pathname}${url.search}`;
  }

  function goToCustomerPage(path) {
    window.location.href = customerPageUrl(path);
  }

  function renderCategoryTabs() {
    if (!categoryTabs) return;
    categoryTabs.innerHTML = categories.map((category) => {
      const count = itemsForCategory(category.id).length;
      if (!count) return "";
      const categoryId = String(category.id);
      return `
        <button class="category-tab ${openCategories.has(categoryId) ? "active" : ""}" data-category-tab="${category.id}" type="button">
          <span>${escapeHtml(category.name)}</span>
          <small>${count}</small>
        </button>
      `;
    }).join("");
  }

  function renderMenu() {
    function itemCard(item) {
      const tags = (item.tags || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
      return `
        <article class="item-card">
          ${imageTag(item)}
          <div class="item-body">
            <div class="item-title">
              <h3>${escapeHtml(item.name)}</h3>
              <span class="price">${money(item.price)}</span>
            </div>
            <p>${escapeHtml(item.description)}</p>
            <div class="tag-row">${tags}</div>
            <button class="button full-width" data-add="${item.id}" type="button">Add to cart</button>
          </div>
        </article>
      `;
    }

    const sections = categories.map((category) => {
      const categoryItems = itemsForCategory(category.id);
      if (!categoryItems.length) return "";
      const categoryId = String(category.id);
      const isSearching = searchInput.value.trim().length > 0;
      const isOpen = isSearching || openCategories.has(categoryId);
      const sectionItems = isOpen
        ? `<div class="menu-section-grid menu-grid">${categoryItems.map(itemCard).join("")}</div>`
        : "";
      return `
        <section class="menu-section ${isOpen ? "open" : ""}" id="category-${category.id}">
          <button class="menu-section-toggle" data-toggle-category="${category.id}" type="button" aria-expanded="${isOpen}">
            <div>
              <h2>${escapeHtml(category.name)}</h2>
              <span class="menu-count">${categoryItems.length} items</span>
            </div>
            <span class="menu-arrow" aria-hidden="true"></span>
          </button>
          ${sectionItems}
        </section>
      `;
    });

    menuList.innerHTML = sections.join("") || `<p class="helper-text">No items found.</p>`;
  }

  function renderCartSummary() {
    const { count, total } = cartStats();
    const formattedTotal = money(total);
    cartCountEls.forEach((element) => {
      element.textContent = String(count);
    });
    checkoutAmountEls.forEach((element) => {
      element.textContent = formattedTotal;
    });
    [
      checkoutShortcutButton,
      mobileCheckoutShortcutButton,
    ].filter(Boolean).forEach((button) => {
      button.disabled = !count;
      button.classList.toggle("is-empty", !count);
    });
  }

  function renderAll() {
    renderCategoryTabs();
    renderMenu();
    renderCartSummary();
  }

  async function loadMenu() {
    const payload = await apiFetch("/api/v1/menu");
    categories = payload.categories;
    items = payload.items;
    renderAll();
  }

  categoryTabs?.addEventListener("click", (event) => {
    const tab = event.target.closest("[data-category-tab]");
    if (!tab) return;
    const categoryId = String(tab.dataset.categoryTab);
    openCategories.add(categoryId);
    renderAll();
    document.getElementById(`category-${categoryId}`)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  });

  menuList.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-toggle-category]");
    if (toggle) {
      const categoryId = String(toggle.dataset.toggleCategory);
      if (openCategories.has(categoryId)) {
        openCategories.delete(categoryId);
      } else {
        openCategories.add(categoryId);
      }
      renderAll();
      document.getElementById(`category-${categoryId}`)?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
      return;
    }

    const button = event.target.closest("[data-add]");
    if (!button) return;
    const id = button.dataset.add;
    cart[id] = (cart[id] || 0) + 1;
    saveCart();
    renderCartSummary();
  });

  cartShortcutButton?.addEventListener("click", () => goToCustomerPage("/cart"));
  mobileCartShortcutButton?.addEventListener("click", () => goToCustomerPage("/cart"));
  checkoutShortcutButton?.addEventListener("click", () => goToCustomerPage("/checkout"));
  mobileCheckoutShortcutButton?.addEventListener("click", () => goToCustomerPage("/checkout"));
  searchInput.addEventListener("input", renderAll);
  loadMenu().catch((error) => {
    menuList.innerHTML = `<p class="helper-text">${escapeHtml(error.message)}</p>`;
  });
}

function initCustomerCartPage() {
  const shell = document.querySelector(".cart-page-shell");
  if (!shell) return;

  const cartKey = "qrCafeCart";
  const tableKey = "qrCafeTableId";
  const customerKey = "qrCafeCustomer";
  const itemNotesKey = "qrCafeItemNotes";
  const cartItemsEl = document.getElementById("cartItems");
  const cartItemSummaryEl = document.getElementById("cartItemSummary");
  const cartSubtotalEl = document.getElementById("cartSubtotal");
  const cartTotalEl = document.getElementById("cartTotal");
  const cartMessage = document.getElementById("cartMessage");
  const clearCartButton = document.getElementById("clearCart");
  const checkoutPageButton = document.getElementById("checkoutPageButton");
  const placeOrderButton = document.getElementById("placeOrder");
  const checkoutMode = shell.dataset.mode === "checkout";
  let tableId = shell.dataset.tableId || localStorage.getItem(tableKey) || null;
  let items = [];
  let cart = JSON.parse(localStorage.getItem(cartKey) || "{}");
  let itemNotes = JSON.parse(localStorage.getItem(itemNotesKey) || "{}");

  if (shell.dataset.tableId) {
    localStorage.setItem(tableKey, shell.dataset.tableId);
    tableId = shell.dataset.tableId;
  }

  function customerPageUrl(path) {
    const url = new URL(path, window.location.origin);
    if (tableId) {
      url.searchParams.set("table", tableId);
    }
    return `${url.pathname}${url.search}`;
  }

  document.querySelectorAll("#continueMenuLink, #cartBackToMenu").forEach((link) => {
    link.setAttribute("href", customerPageUrl("/menu"));
  });

  function saveCart() {
    localStorage.setItem(cartKey, JSON.stringify(cart));
  }

  function saveItemNotes() {
    localStorage.setItem(itemNotesKey, JSON.stringify(itemNotes));
  }

  function cartStats() {
    return Object.entries(cart).reduce((stats, [id, quantity]) => {
      const item = items.find((candidate) => String(candidate.id) === String(id));
      if (!item || quantity <= 0) return stats;
      stats.count += quantity;
      stats.total += item.price * quantity;
      return stats;
    }, { count: 0, total: 0 });
  }

  function renderCart() {
    const rows = Object.entries(cart).map(([id, quantity]) => {
      const item = items.find((candidate) => String(candidate.id) === String(id));
      if (!item || quantity <= 0) return "";
      const lineTotal = Number(item.price || 0) * quantity;
      const noteField = checkoutMode
        ? `<label class="item-note-field">
            Special instructions
            <textarea data-item-note="${id}" maxlength="240" placeholder="Less sugar, no onion, extra spicy...">${escapeHtml(itemNotes[id] || "")}</textarea>
          </label>`
        : "";
      return `
        <div class="cart-row cart-page-row">
          ${imageTag(item, "cart-thumb")}
          <div class="cart-line-main">
            <strong>${escapeHtml(item.name)}</strong>
            <p class="helper-text">${money(item.price)} each</p>
            <button class="link-button remove-line" data-remove-item="${id}" type="button">Remove item</button>
            ${noteField}
          </div>
          <div class="cart-line-side">
            <strong>${money(lineTotal)}</strong>
            <div class="stepper" aria-label="Quantity for ${escapeHtml(item.name)}">
              <button type="button" data-step="${id}" data-delta="-1">-</button>
              <span>${quantity}</span>
              <button type="button" data-step="${id}" data-delta="1">+</button>
            </div>
          </div>
        </div>
      `;
    }).join("");
    const { count, total } = cartStats();
    cartItemSummaryEl.textContent = `${count} item${count === 1 ? "" : "s"} in this order`;
    cartItemsEl.innerHTML = rows || `
      <div class="empty-cart-state">
        <p class="helper-text">Your cart is empty.</p>
        <a class="button" href="${customerPageUrl("/menu")}">Browse menu</a>
      </div>
    `;
    cartSubtotalEl.textContent = money(total);
    cartTotalEl.textContent = money(total);
    clearCartButton.disabled = !count;
    checkoutPageButton?.toggleAttribute("disabled", !count);
    placeOrderButton?.toggleAttribute("disabled", !count);
    if (checkoutMode && !count) {
      cartMessage.textContent = "Add items from the menu before checkout.";
    } else if (!cartMessage.textContent.includes("Creating order")) {
      cartMessage.textContent = "";
    }
  }

  async function verifyMockPayment(order, payment) {
    cartMessage.textContent = "Confirming mock payment...";
    const confirmed = await apiFetch("/api/v1/payments/razorpay/verify", {
      method: "POST",
      body: {
        provider_order_id: payment.provider_order_id,
        provider_payment_id: `mock_pay_${Date.now()}`,
      },
    });
    cart = {};
    itemNotes = {};
    saveCart();
    saveItemNotes();
    window.location.href = `/order/${confirmed.id || order.id}`;
  }

  function openRazorpayCheckout(order, payment) {
    if (payment.mode === "mock" || !window.Razorpay) {
      verifyMockPayment(order, payment).catch((error) => {
        cartMessage.textContent = error.message;
      });
      return;
    }

    const checkout = new window.Razorpay({
      key: payment.key_id,
      amount: payment.amount,
      currency: payment.currency,
      name: cafeName,
      description: order.order_number,
      order_id: payment.provider_order_id,
      handler: async (response) => {
        const confirmed = await apiFetch("/api/v1/payments/razorpay/verify", {
          method: "POST",
          body: {
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          },
        });
        cart = {};
        itemNotes = {};
        saveCart();
        saveItemNotes();
        window.location.href = `/order/${confirmed.id}`;
      },
      modal: {
        ondismiss: () => {
          cartMessage.textContent = "Payment was not completed. Your order is waiting for payment.";
        },
      },
    });
    checkout.open();
  }

  async function placeOrder() {
    const orderItems = Object.entries(cart)
      .filter(([id, quantity]) => quantity > 0 && items.some((item) => String(item.id) === String(id)))
      .map(([menu_item_id, quantity]) => ({
        menu_item_id: Number(menu_item_id),
        quantity,
        note: itemNotes[menu_item_id] || "",
      }));
    if (!orderItems.length) {
      cartMessage.textContent = "Add at least one item first.";
      return;
    }

    placeOrderButton.disabled = true;
    cartMessage.textContent = "Creating order...";
    try {
      const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked')?.value || "cash";
      const customerName = document.getElementById("customerName").value;
      const customerPhone = document.getElementById("customerPhone").value;
      localStorage.setItem(customerKey, JSON.stringify({
        name: customerName,
        phone: customerPhone,
      }));
      const order = await apiFetch("/api/v1/orders", {
        method: "POST",
        body: {
          table_id: tableId,
          customer_name: customerName,
          customer_phone: customerPhone,
          notes: document.getElementById("orderNotes").value,
          payment_method: paymentMethod,
          items: orderItems,
        },
      });

      if (order.payment) {
        openRazorpayCheckout(order, order.payment);
      } else {
        cart = {};
        itemNotes = {};
        saveCart();
        saveItemNotes();
        window.location.href = `/order/${order.id}`;
      }
    } catch (error) {
      cartMessage.textContent = error.message;
      placeOrderButton.disabled = false;
    }
  }

  cartItemsEl.addEventListener("click", (event) => {
    const removeButton = event.target.closest("[data-remove-item]");
    if (removeButton) {
      delete cart[removeButton.dataset.removeItem];
      delete itemNotes[removeButton.dataset.removeItem];
      saveCart();
      saveItemNotes();
      renderCart();
      return;
    }

    const button = event.target.closest("[data-step]");
    if (!button) return;
    const id = button.dataset.step;
    cart[id] = (cart[id] || 0) + Number(button.dataset.delta);
    if (cart[id] <= 0) {
      delete cart[id];
      delete itemNotes[id];
    }
    saveCart();
    saveItemNotes();
    renderCart();
  });

  cartItemsEl.addEventListener("input", (event) => {
    const noteInput = event.target.closest("[data-item-note]");
    if (!noteInput) return;
    itemNotes[noteInput.dataset.itemNote] = noteInput.value.trim();
    saveItemNotes();
  });

  clearCartButton.addEventListener("click", () => {
    cart = {};
    itemNotes = {};
    saveCart();
    saveItemNotes();
    renderCart();
  });

  checkoutPageButton?.addEventListener("click", () => {
    const { count } = cartStats();
    if (!count) {
      cartMessage.textContent = "Add at least one item first.";
      return;
    }
    window.location.href = customerPageUrl("/checkout");
  });
  placeOrderButton?.addEventListener("click", placeOrder);

  apiFetch("/api/v1/menu").then((payload) => {
    items = payload.items;
    const savedCustomer = JSON.parse(localStorage.getItem(customerKey) || "{}");
    if (checkoutMode) {
      const nameField = document.getElementById("customerName");
      const phoneField = document.getElementById("customerPhone");
      if (nameField && savedCustomer.name) nameField.value = savedCustomer.name;
      if (phoneField && savedCustomer.phone) phoneField.value = savedCustomer.phone;
    }
    renderCart();
    if (checkoutMode && cartStats().count) {
      window.setTimeout(() => document.getElementById("customerName")?.focus(), 250);
    }
  }).catch((error) => {
    cartItemsEl.innerHTML = `<p class="helper-text">${escapeHtml(error.message)}</p>`;
  });
}

function orderDetailsHtml(order) {
  const lines = order.items.map((item) => (
    `<div class="receipt-item">
      <span>${escapeHtml(item.item_name)} x ${item.quantity}</span>
      <strong>${money(item.line_total)}</strong>
    </div>`
  )).join("");
  return `
    <div class="order-detail-grid">
      <p><strong>Status</strong><span>${escapeHtml(order.status.replaceAll("_", " "))}</span></p>
      <p><strong>Payment</strong><span>${escapeHtml(order.payment_status.replaceAll("_", " "))}</span></p>
      <p><strong>Table</strong><span>${escapeHtml(order.table_label || "Takeaway")}</span></p>
      <p><strong>Total</strong><span>${money(order.total_amount)}</span></p>
    </div>
    <div class="receipt-items">${lines}</div>
  `;
}

function estimatedWaitLabel(order) {
  if (order.status === "ready") return "Ready now";
  if (order.status === "completed") return "Completed";
  if (order.status === "cancelled") return "Order cancelled";
  if (order.status === "preparing") return "Estimated wait: 8-12 minutes";
  if (order.status === "payment_pending") return "Confirm payment to receive a token";
  return "Estimated wait: 12-18 minutes";
}

function whatsappConfirmationUrl(order) {
  const token = order.token_number ? `Token ${order.token_number}` : "Payment pending";
  const table = order.table_label ? `Table: ${order.table_label}` : "Table: Takeaway";
  const items = order.items.map((item) => `${item.item_name} x ${item.quantity}`).join(", ");
  const message = [
    `${cafeName} order confirmation`,
    `Order: ${order.order_number}`,
    token,
    table,
    `Items: ${items}`,
    `Total: ${money(order.total_amount)}`,
  ].join("\n");
  return `https://wa.me/?text=${encodeURIComponent(message)}`;
}

function initOrderStatus() {
  const panel = document.querySelector(".token-panel");
  if (!panel) return;
  const orderId = panel.dataset.orderId;
  const tokenNumber = document.getElementById("tokenNumber");
  const tokenStatus = document.getElementById("tokenStatus");
  const details = document.getElementById("orderStatusDetails");
  const estimatedWait = document.getElementById("estimatedWait");
  const whatsAppLink = document.getElementById("whatsAppConfirmLink");

  function render(order) {
    tokenNumber.textContent = order.token_number ? `Token ${order.token_number}` : "Payment pending";
    tokenStatus.textContent = order.status.replaceAll("_", " ");
    tokenStatus.className = `status-pill status-${order.status}`;
    estimatedWait.textContent = estimatedWaitLabel(order);
    whatsAppLink.href = whatsappConfirmationUrl(order);
    details.innerHTML = orderDetailsHtml(order);
  }

  async function refresh() {
    const order = await apiFetch(`/api/v1/orders/${orderId}`);
    render(order);
  }

  const socket = connectSocket();
  if (socket) {
    socket.emit("customer_join", { order_id: orderId });
    socket.on("order_updated", render);
  } else {
    setInterval(refresh, 5000);
  }
  refresh().catch(() => {});
}

function initAdminDashboard() {
  const board = document.getElementById("ordersBoard");
  if (!board) return;
  const dashboard = document.querySelector(".metric-grid");
  const filter = document.getElementById("orderStatusFilter");
  const salesRange = document.getElementById("salesRange");
  const recentBody = document.getElementById("recentOrdersBody");
  const topItemsList = document.getElementById("topItemsList");
  const salesChart = document.getElementById("salesChart");
  const alertsButton = document.getElementById("enableAlertsButton");
  const alertsStatus = document.getElementById("alertsStatus");
  const orderDialog = document.getElementById("orderDetailDialog");
  const orderDetailTitle = document.getElementById("orderDetailTitle");
  const orderDetailBody = document.getElementById("orderDetailBody");
  const tableLimit = Number(dashboard?.dataset.tableCount || 0);
  const statusValues = ["pending", "preparing", "ready", "completed", "cancelled"];
  const seenOrdersKey = "qrCafeSeenOrders";
  let orders = [];
  let tables = [];
  let isLoading = false;
  let dashboardDataSignature = "";
  let seenOrderIds = new Set(JSON.parse(localStorage.getItem(seenOrdersKey) || "[]"));
  let alertsEnabled = localStorage.getItem("qrCafeAdminAlerts") === "on";
  let alertAudioContext = null;

  function renderAlertState() {
    if (!alertsButton || !alertsStatus) return;
    alertsButton.textContent = alertsEnabled ? "Sound on" : "Enable sound";
    alertsButton.classList.toggle("primary", alertsEnabled);
    alertsStatus.textContent = alertsEnabled
      ? "Sound and desktop alerts are on"
      : "Sound alerts are off";
  }

  function ensureAlertAudio() {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return null;
    if (!alertAudioContext) {
      alertAudioContext = new AudioContext();
    }
    if (alertAudioContext.state === "suspended") {
      alertAudioContext.resume().catch(() => {});
    }
    return alertAudioContext;
  }

  function playKitchenTone() {
    if (!alertsEnabled) return;
    const audio = ensureAlertAudio();
    if (!audio) return;
    const start = audio.currentTime + 0.02;
    [784, 988, 1175].forEach((frequency, index) => {
      const oscillator = audio.createOscillator();
      const gain = audio.createGain();
      oscillator.type = "sine";
      oscillator.frequency.value = frequency;
      gain.gain.setValueAtTime(0.0001, start + index * 0.16);
      gain.gain.exponentialRampToValueAtTime(0.28, start + index * 0.16 + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, start + index * 0.16 + 0.14);
      oscillator.connect(gain).connect(audio.destination);
      oscillator.start(start + index * 0.16);
      oscillator.stop(start + index * 0.16 + 0.16);
    });
  }

  function announceNewOrder() {
    if (!alertsEnabled || !("speechSynthesis" in window) || !("SpeechSynthesisUtterance" in window)) return;
    window.speechSynthesis.cancel();
    const message = new SpeechSynthesisUtterance("New order");
    message.lang = "en-IN";
    message.rate = 0.95;
    message.pitch = 1.05;
    message.volume = 1;
    window.speechSynthesis.speak(message);
  }

  function showOrderNotification(order) {
    if (!alertsEnabled || !("Notification" in window) || Notification.permission !== "granted") return;
    const itemCount = (order.items || []).reduce((sum, item) => sum + Number(item.quantity || 0), 0);
    new Notification(`New order ${order.order_number}`, {
      body: `${order.table_label || "No table"} - ${itemCount} item${itemCount === 1 ? "" : "s"} - ${money(order.total_amount)}`,
      icon: "/static/brand/tea_trust_logo.png",
    });
  }

  async function enableAlerts() {
    alertsEnabled = true;
    localStorage.setItem("qrCafeAdminAlerts", "on");
    ensureAlertAudio();
    if ("Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission().catch(() => {});
    }
    renderAlertState();
    playKitchenTone();
  }

  function dashboardMoney(value) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(Number(value || 0));
  }

  function statusLabel(status) {
    return String(status || "").replaceAll("_", " ");
  }

  function statusSelectHtml(order) {
    const values = order.status === "payment_pending"
      ? ["payment_pending", ...statusValues]
      : statusValues;
    return `
      <select class="status-select status-${order.status}" data-status-for="${order.id}" aria-label="Order status" ${order.status === "payment_pending" ? "disabled" : ""}>
        ${values.map((status) => (
          `<option value="${status}" ${status === order.status ? "selected" : ""}>${statusLabel(status)}</option>`
        )).join("")}
      </select>
    `;
  }

  function saveSeenOrders() {
    localStorage.setItem(seenOrdersKey, JSON.stringify([...seenOrderIds].slice(-300)));
  }

  function isUnseen(order) {
    return !seenOrderIds.has(Number(order.id)) && ["pending", "preparing", "ready"].includes(order.status);
  }

  function quickStatusButtons(order) {
    const actions = [];
    if (order.status === "pending") {
      actions.push(["preparing", "Accept"]);
      actions.push(["cancelled", "Cancel"]);
    } else if (order.status === "preparing") {
      actions.push(["ready", "Ready"]);
      actions.push(["cancelled", "Cancel"]);
    } else if (order.status === "ready") {
      actions.push(["completed", "Complete"]);
    } else if (order.status === "payment_pending") {
      actions.push(["cancelled", "Cancel"]);
    }
    return actions.map(([status, label]) => (
      `<button class="button mini-button ${status === "cancelled" ? "danger" : ""}" data-quick-status="${status}" data-order-id="${order.id}" type="button">${label}</button>`
    )).join("");
  }

  async function updateOrderStatus(orderId, status, cancellationReason = "") {
    await apiFetch(`/api/v1/admin/orders/${orderId}/status`, {
      method: "PATCH",
      body: {
        status,
        cancellation_reason: cancellationReason,
      },
    });
    await load();
  }

  function orderNotesHtml(order) {
    return order.notes
      ? `<pre class="order-notes">${escapeHtml(order.notes)}</pre>`
      : `<p class="helper-text">No notes.</p>`;
  }

  function renderOrderDetail(order) {
    const items = (order.items || []).map((item) => `
      <div class="receipt-item">
        <span>${escapeHtml(item.item_name)} x ${item.quantity}</span>
        <strong>${money(item.line_total)}</strong>
      </div>
    `).join("");
    const statusActions = quickStatusButtons(order);
    orderDetailTitle.textContent = `${order.order_number} - ${order.table_label || "No table"}`;
    orderDetailBody.innerHTML = `
      <div class="order-detail-grid">
        <p><strong>Customer</strong><span>${escapeHtml(order.customer_name || "Guest")}</span></p>
        <p><strong>Phone</strong><span>${escapeHtml(order.customer_phone || "Not shared")}</span></p>
        <p><strong>Payment</strong><span>${escapeHtml(order.payment_method)} / ${escapeHtml(order.payment_status.replaceAll("_", " "))}</span></p>
        <p><strong>Total</strong><span>${money(order.total_amount)}</span></p>
      </div>
      <div class="receipt-items">${items}</div>
      <section class="order-notes-section">
        <h3>Notes</h3>
        ${orderNotesHtml(order)}
      </section>
      <section class="modal-actions">
        ${statusActions || `<p class="helper-text">No quick actions for this status.</p>`}
      </section>
      <label class="cancel-reason-field">
        Cancellation reason
        <textarea id="modalCancelReason" maxlength="240" placeholder="Only needed when cancelling"></textarea>
      </label>
    `;
  }

  function openOrderDetail(orderId) {
    const order = orders.find((candidate) => String(candidate.id) === String(orderId));
    if (!order || !orderDialog) return;
    seenOrderIds.add(Number(order.id));
    saveSeenOrders();
    render();
    renderOrderDetail(order);
    orderDialog.showModal();
  }

  function timeAgo(value) {
    const created = new Date(value);
    const seconds = Math.max(0, Math.floor((Date.now() - created.getTime()) / 1000));
    if (seconds < 60) return "Just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} min${minutes === 1 ? "" : "s"} ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hr${hours === 1 ? "" : "s"} ago`;
    const days = Math.floor(hours / 24);
    return `${days} day${days === 1 ? "" : "s"} ago`;
  }

  function dateKey(value) {
    const date = new Date(value);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  }

  function shortDate(date) {
    return new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short" }).format(date);
  }

  function filteredOrders() {
    const status = filter?.value || "";
    return status ? orders.filter((order) => order.status === status) : orders;
  }

  function activeRevenueOrders() {
    return orders.filter((order) => (
      order.status !== "cancelled" &&
      order.payment_status !== "created" &&
      order.payment_status !== "failed"
    ));
  }

  function renderMetrics() {
    const revenue = activeRevenueOrders().reduce((sum, order) => sum + Number(order.total_amount || 0), 0);
    const pending = orders.filter((order) => ["pending", "payment_pending"].includes(order.status)).length;
    const tokenOrders = orders.filter((order) => order.token_number);
    const completedTokens = tokenOrders.filter((order) => order.status === "completed").length;
    const pendingTokens = tokenOrders.filter((order) => ["pending", "preparing", "ready"].includes(order.status)).length;
    const cancelledTokens = tokenOrders.filter((order) => order.status === "cancelled").length;
    const totalTokens = tokenOrders.length;
    const lastToken = tokenOrders.reduce((max, order) => Math.max(max, Number(order.token_number || 0)), 0);
    const tokenPercent = totalTokens ? Math.round((completedTokens / totalTokens) * 100) : 0;

    document.getElementById("totalOrdersMetric").textContent = orders.length;
    document.getElementById("totalRevenueMetric").textContent = dashboardMoney(revenue);
    document.getElementById("pendingOrdersMetric").textContent = pending;
    document.getElementById("activeTablesMetric").textContent = `${tables.length} / ${tableLimit || tables.length}`;
    document.getElementById("lastTokenMetric").textContent = lastToken ? `#${String(lastToken).padStart(4, "0")}` : "#0000";
    document.getElementById("totalTokensMetric").textContent = totalTokens;
    document.getElementById("completedTokensMetric").textContent = completedTokens;
    document.getElementById("pendingTokensMetric").textContent = pendingTokens;
    document.getElementById("cancelledTokensMetric").textContent = cancelledTokens;
    document.getElementById("tokenPercentMetric").textContent = `${tokenPercent}%`;
    document.getElementById("tokenProgressBar").style.width = `${tokenPercent}%`;
    document.getElementById("ordersTrend").textContent = orders.length === 1 ? "1 live order" : `${orders.length} live orders`;
  }

  function renderTopItems() {
    const items = new Map();
    activeRevenueOrders().forEach((order) => {
      (order.items || []).forEach((item) => {
        const current = items.get(item.item_name) || {
          name: item.item_name,
          quantity: 0,
          revenue: 0,
          id: item.menu_item_id,
        };
        current.quantity += Number(item.quantity || 0);
        current.revenue += Number(item.line_total || 0);
        items.set(item.item_name, current);
      });
    });

    const topItems = [...items.values()]
      .sort((a, b) => b.quantity - a.quantity || b.revenue - a.revenue)
      .slice(0, 5);

    topItemsList.innerHTML = topItems.map((item, index) => {
      const imageItem = {
        id: item.id,
        name: item.name,
        category_name: "",
        tags: [],
        image_url: "",
      };
      return `
        <article class="top-item">
          <span class="rank-badge">${index + 1}</span>
          ${imageTag(imageItem, "top-thumb")}
          <span class="top-item-name">
            <strong>${escapeHtml(item.name)}</strong>
            <small>${item.quantity}+ orders</small>
          </span>
          <strong>${dashboardMoney(item.revenue)}</strong>
        </article>
      `;
    }).join("") || `<p class="helper-text">No item sales yet.</p>`;
  }

  function renderSalesChart() {
    const days = Number(salesRange?.value || 7);
    const width = 720;
    const height = 280;
    const left = 70;
    const right = 20;
    const top = 24;
    const bottom = 42;
    const chartWidth = width - left - right;
    const chartHeight = height - top - bottom;
    const buckets = [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (let index = days - 1; index >= 0; index -= 1) {
      const date = new Date(today);
      date.setDate(today.getDate() - index);
      buckets.push({ key: dateKey(date), label: shortDate(date), value: 0 });
    }

    const byKey = new Map(buckets.map((bucket) => [bucket.key, bucket]));
    activeRevenueOrders().forEach((order) => {
      const bucket = byKey.get(dateKey(order.created_at));
      if (bucket) bucket.value += Number(order.total_amount || 0);
    });

    const maxValue = Math.max(100, ...buckets.map((bucket) => bucket.value));
    const points = buckets.map((bucket, index) => {
      const x = left + (chartWidth * index) / Math.max(1, buckets.length - 1);
      const y = top + chartHeight - (bucket.value / maxValue) * chartHeight;
      return { ...bucket, x, y };
    });
    const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" ");
    const area = `${path} L ${points.at(-1).x.toFixed(2)} ${top + chartHeight} L ${points[0].x.toFixed(2)} ${top + chartHeight} Z`;
    const grid = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
      const y = top + chartHeight - ratio * chartHeight;
      const value = Math.round(maxValue * ratio);
      return `
        <line x1="${left}" y1="${y}" x2="${width - right}" y2="${y}" />
        <text x="12" y="${y + 5}">${dashboardMoney(value)}</text>
      `;
    }).join("");
    const labels = points.map((point) => `<text class="x-label" x="${point.x}" y="${height - 10}">${point.label}</text>`).join("");
    const circles = points.map((point) => `<circle cx="${point.x}" cy="${point.y}" r="5"><title>${point.label}: ${dashboardMoney(point.value)}</title></circle>`).join("");

    salesChart.innerHTML = `
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Revenue over time">
        <g class="chart-grid">${grid}</g>
        <path class="chart-area" d="${area}"></path>
        <path class="chart-line" d="${path}"></path>
        <g class="chart-points">${circles}</g>
        <g class="chart-labels">${labels}</g>
      </svg>
    `;
  }

  function render() {
    const visibleOrders = filteredOrders();
    if (recentBody) {
      recentBody.innerHTML = visibleOrders.slice(0, 8).map((order) => {
        const itemsCount = (order.items || []).reduce((sum, item) => sum + Number(item.quantity || 0), 0);
        return `
          <tr class="${isUnseen(order) ? "is-unseen" : ""}">
            <td><strong>${escapeHtml(order.order_number)}</strong></td>
            <td>${escapeHtml(order.table_label || "No table")}</td>
            <td>${itemsCount} item${itemsCount === 1 ? "" : "s"}</td>
            <td>${dashboardMoney(order.total_amount)}</td>
            <td>${statusSelectHtml(order)}</td>
            <td>${timeAgo(order.created_at)}</td>
            <td>
              <div class="order-inline-actions">
                <button class="button mini-button" data-view-order="${order.id}" type="button">View</button>
                <button class="button mini-button" data-save-status="${order.id}" type="button" ${order.status === "payment_pending" ? "disabled" : ""}>Save</button>
                ${quickStatusButtons(order)}
              </div>
            </td>
          </tr>
        `;
      }).join("") || `<tr><td colspan="7" class="empty-cell">No orders found.</td></tr>`;
    }

    board.innerHTML = visibleOrders.slice(0, 8).map((order) => {
      const items = order.items.map((item) => `<li>${escapeHtml(item.item_name)} x ${item.quantity}</li>`).join("");
      return `
        <article class="order-card ${isUnseen(order) ? "is-unseen" : ""}" data-order-id="${order.id}">
          <header>
            <div>
              <strong>${escapeHtml(order.order_number)}</strong>
              <p class="helper-text">${escapeHtml(order.table_label || "No table")} - ${money(order.total_amount)}</p>
            </div>
            <span class="status-pill status-${order.status}">${escapeHtml(order.status.replaceAll("_", " "))}</span>
          </header>
          <p><strong>Token:</strong> ${order.token_number || "Pending payment"}</p>
          <ul>${items}</ul>
          <div class="order-actions">
            ${statusSelectHtml(order)}
            <button class="button" data-save-status="${order.id}" type="button" ${order.status === "payment_pending" ? "disabled" : ""}>Update</button>
            <button class="button" data-view-order="${order.id}" type="button">View</button>
            ${quickStatusButtons(order)}
          </div>
        </article>
      `;
    }).join("") || `<p class="helper-text">No orders found.</p>`;

    renderMetrics();
    renderTopItems();
    renderSalesChart();
  }

  async function load() {
    if (isLoading) return;
    isLoading = true;
    try {
      const [orderPayload, tablePayload] = await Promise.all([
        apiFetch("/api/v1/admin/orders"),
        apiFetch("/api/v1/admin/tables"),
      ]);
      const nextSignature = JSON.stringify({ orders: orderPayload, tables: tablePayload });
      if (nextSignature === dashboardDataSignature) {
        return;
      }
      dashboardDataSignature = nextSignature;
      orders = orderPayload;
      tables = tablePayload;
      render();
    } finally {
      isLoading = false;
    }
  }

  document.querySelector(".recent-orders-panel")?.addEventListener("click", async (event) => {
    const viewButton = event.target.closest("[data-view-order]");
    if (viewButton) {
      openOrderDetail(viewButton.dataset.viewOrder);
      return;
    }

    const quickButton = event.target.closest("[data-quick-status]");
    if (quickButton) {
      const reason = quickButton.dataset.quickStatus === "cancelled"
        ? window.prompt("Reason for cancellation?") || ""
        : "";
      await updateOrderStatus(quickButton.dataset.orderId, quickButton.dataset.quickStatus, reason);
      return;
    }

    const button = event.target.closest("[data-save-status]");
    if (!button) return;
    const orderId = button.dataset.saveStatus;
    const scope = button.closest("tr") || button.closest(".order-card") || document;
    const select = scope.querySelector(`[data-status-for="${orderId}"]`);
    if (!select) return;
    await updateOrderStatus(orderId, select.value);
  });

  orderDetailBody?.addEventListener("click", async (event) => {
    const quickButton = event.target.closest("[data-quick-status]");
    if (!quickButton) return;
    const reason = quickButton.dataset.quickStatus === "cancelled"
      ? document.getElementById("modalCancelReason")?.value || window.prompt("Reason for cancellation?") || ""
      : "";
    await updateOrderStatus(quickButton.dataset.orderId, quickButton.dataset.quickStatus, reason);
    orderDialog?.close();
  });

  filter?.addEventListener("change", render);
  salesRange?.addEventListener("change", renderSalesChart);
  alertsButton?.addEventListener("click", enableAlerts);
  renderAlertState();
  const socket = connectSocket();
  if (socket) {
    socket.emit("admin_join");
    socket.on("order_created", (order) => {
      playKitchenTone();
      announceNewOrder();
      showOrderNotification(order);
      load();
    });
    socket.on("order_updated", load);
  }
  setInterval(load, 3000);
  load().catch((error) => {
    board.innerHTML = `<p class="helper-text">${escapeHtml(error.message)}</p>`;
  });
}

function adminMoney(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

function kitchenOrderCard(order) {
  const items = (order.items || []).map((item) => `<li>${escapeHtml(item.item_name)} x ${item.quantity}</li>`).join("");
  const actions = {
    pending: [["preparing", "Accept"]],
    preparing: [["ready", "Ready"]],
    ready: [["completed", "Complete"]],
  }[order.status] || [];
  return `
    <article class="kitchen-card">
      <header>
        <span>${order.token_number ? `#${String(order.token_number).padStart(3, "0")}` : "Pay"}</span>
        <strong>${escapeHtml(order.table_label || "No table")}</strong>
      </header>
      <p>${escapeHtml(order.order_number)} - ${money(order.total_amount)}</p>
      <ul>${items}</ul>
      ${order.notes ? `<pre>${escapeHtml(order.notes)}</pre>` : ""}
      <div class="order-actions">
        ${actions.map(([status, label]) => `<button class="button primary" data-kitchen-status="${status}" data-order-id="${order.id}" type="button">${label}</button>`).join("")}
      </div>
    </article>
  `;
}

function initKitchenDisplay() {
  const board = document.querySelector(".kitchen-board");
  if (!board) return;
  const columns = {
    pending: document.getElementById("kitchenPending"),
    preparing: document.getElementById("kitchenPreparing"),
    ready: document.getElementById("kitchenReady"),
  };
  const counts = {
    pending: document.getElementById("kitchenPendingCount"),
    preparing: document.getElementById("kitchenPreparingCount"),
    ready: document.getElementById("kitchenReadyCount"),
  };
  let signature = "";

  function render(orders) {
    Object.entries(columns).forEach(([status, element]) => {
      const statusOrders = orders.filter((order) => order.status === status);
      counts[status].textContent = statusOrders.length;
      element.innerHTML = statusOrders.map(kitchenOrderCard).join("") || `<p class="helper-text">No ${status.replaceAll("_", " ")} orders.</p>`;
    });
  }

  async function load() {
    const orders = await apiFetch("/api/v1/admin/orders");
    const active = orders.filter((order) => ["pending", "preparing", "ready"].includes(order.status));
    const nextSignature = JSON.stringify(active);
    if (nextSignature === signature) return;
    signature = nextSignature;
    render(active);
  }

  board.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-kitchen-status]");
    if (!button) return;
    await apiFetch(`/api/v1/admin/orders/${button.dataset.orderId}/status`, {
      method: "PATCH",
      body: { status: button.dataset.kitchenStatus },
    });
    signature = "";
    await load();
  });

  const socket = connectSocket();
  if (socket) {
    socket.emit("admin_join");
    socket.on("order_created", load);
    socket.on("order_updated", load);
  }
  setInterval(load, 5000);
  load().catch(() => {});
}

function analyticsLineChart(points) {
  const width = 720;
  const height = 280;
  const left = 70;
  const right = 22;
  const top = 22;
  const bottom = 42;
  const chartWidth = width - left - right;
  const chartHeight = height - top - bottom;
  const maxValue = Math.max(100, ...points.map((point) => point.revenue));
  const plotted = points.map((point, index) => {
    const x = left + (chartWidth * index) / Math.max(1, points.length - 1);
    const y = top + chartHeight - (point.revenue / maxValue) * chartHeight;
    return { ...point, x, y };
  });
  const path = plotted.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" ");
  const area = `${path} L ${plotted.at(-1).x.toFixed(2)} ${top + chartHeight} L ${plotted[0].x.toFixed(2)} ${top + chartHeight} Z`;
  const labels = plotted.map((point) => {
    const label = new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short" }).format(new Date(point.date));
    return `<text class="x-label" x="${point.x}" y="${height - 10}">${label}</text>`;
  }).join("");
  return `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Revenue by day">
      <path class="chart-area" d="${area}"></path>
      <path class="chart-line" d="${path}"></path>
      <g class="chart-points">${plotted.map((point) => `<circle cx="${point.x}" cy="${point.y}" r="5"><title>${adminMoney(point.revenue)}</title></circle>`).join("")}</g>
      <g class="chart-labels">${labels}</g>
    </svg>
  `;
}

function initAdminAnalytics() {
  const range = document.getElementById("analyticsRange");
  if (!range) return;
  const dailyChart = document.getElementById("analyticsDailyChart");
  const topItems = document.getElementById("analyticsTopItems");
  const hourly = document.getElementById("analyticsHourly");

  function render(payload) {
    document.getElementById("analyticsRevenue").textContent = adminMoney(payload.revenue);
    document.getElementById("analyticsOrders").textContent = payload.order_count;
    document.getElementById("analyticsAov").textContent = `Average ${adminMoney(payload.average_order_value)}`;
    document.getElementById("analyticsPeakHour").textContent = payload.peak_hour === null
      ? "--"
      : `${String(payload.peak_hour).padStart(2, "0")}:00`;
    document.getElementById("analyticsPrepTime").textContent = payload.average_prep_minutes === null
      ? "--"
      : `${payload.average_prep_minutes} min`;
    dailyChart.innerHTML = analyticsLineChart(payload.daily || []);
    topItems.innerHTML = (payload.top_items || []).map((item, index) => `
      <article class="top-item">
        <span class="rank-badge">${index + 1}</span>
        ${imageTag({ name: item.name, category_name: "", tags: [], image_url: "" }, "top-thumb")}
        <span class="top-item-name">
          <strong>${escapeHtml(item.name)}</strong>
          <small>${item.quantity} sold</small>
        </span>
        <strong>${adminMoney(item.revenue)}</strong>
      </article>
    `).join("") || `<p class="helper-text">No sales yet.</p>`;
    const maxOrders = Math.max(1, ...(payload.hourly || []).map((bucket) => bucket.orders));
    hourly.innerHTML = (payload.hourly || []).map((bucket) => `
      <div class="hourly-bar">
        <span>${String(bucket.hour).padStart(2, "0")}</span>
        <strong style="height: ${Math.max(4, (bucket.orders / maxOrders) * 100)}%"></strong>
        <small>${bucket.orders}</small>
      </div>
    `).join("");
  }

  async function load() {
    const payload = await apiFetch(`/api/v1/admin/analytics?days=${range.value}`);
    render(payload);
  }

  range.addEventListener("change", load);
  load().catch((error) => {
    dailyChart.innerHTML = `<p class="helper-text">${escapeHtml(error.message)}</p>`;
  });
}

function initAdminMenu() {
  const list = document.getElementById("menuAdminList");
  if (!list) return;
  const categoryForm = document.getElementById("categoryForm");
  const itemForm = document.getElementById("menuItemForm");
  const categorySelect = document.getElementById("itemCategorySelect");
  const categoryFilter = document.getElementById("menuAdminCategoryFilter");
  const searchInput = document.getElementById("menuAdminSearch");
  const summary = document.getElementById("menuAdminSummary");
  const refreshButton = document.getElementById("refreshMenuAdmin");
  let categories = [];
  let items = [];

  async function load() {
    const payload = await apiFetch("/api/v1/menu?include_unavailable=1");
    categories = payload.categories;
    items = payload.items;
    categorySelect.innerHTML = categories.map((category) => (
      `<option value="${category.id}">${escapeHtml(category.name)}</option>`
    )).join("");
    categoryFilter.innerHTML = `
      <option value="">All categories</option>
      ${categories.map((category) => `<option value="${category.id}">${escapeHtml(category.name)}</option>`).join("")}
    `;
    render();
  }

  function filteredItems() {
    const query = (searchInput?.value || "").trim().toLowerCase();
    const categoryId = categoryFilter?.value || "";
    return items.filter((item) => {
      const matchesCategory = !categoryId || String(item.category_id) === String(categoryId);
      const haystack = `${item.name} ${item.description} ${item.category_name} ${(item.tags || []).join(" ")}`.toLowerCase();
      return matchesCategory && (!query || haystack.includes(query));
    });
  }

  function render() {
    const visibleItems = filteredItems();
    summary.textContent = `${visibleItems.length} of ${items.length} item${items.length === 1 ? "" : "s"} shown`;
    list.innerHTML = visibleItems.map((item) => `
      <article class="admin-row" data-item="${item.id}">
        <div class="admin-menu-item-shell">
          <div class="admin-image-cell">
            ${imageTag(item, "admin-menu-thumb")}
            <span class="helper-text">${escapeHtml(item.category_name || "Uncategorized")}</span>
          </div>
          <div>
        <div class="admin-row-grid">
          <input name="name" value="${escapeHtml(item.name)}" aria-label="Item name">
          <textarea name="description" aria-label="Description">${escapeHtml(item.description)}</textarea>
          <input name="price" type="number" min="0" step="0.01" value="${item.price}" aria-label="Price">
          <select name="category_id" aria-label="Category">
            ${categories.map((category) => `<option value="${category.id}" ${category.id === item.category_id ? "selected" : ""}>${escapeHtml(category.name)}</option>`).join("")}
          </select>
        </div>
        <div class="row-actions">
          <label class="check-row"><input type="checkbox" name="is_available" ${item.is_available ? "checked" : ""}> Available</label>
          <label class="check-row"><input type="checkbox" name="is_veg" ${item.is_veg ? "checked" : ""}> Veg</label>
          <label class="check-row"><input type="checkbox" name="is_bestseller" ${item.is_bestseller ? "checked" : ""}> Bestseller</label>
          <input name="tags" value="${escapeHtml((item.tags || []).join(", "))}" aria-label="Tags">
          <input name="image" type="file" accept="image/png,image/jpeg,image/webp" aria-label="Upload image">
          <button class="button" data-save-item="${item.id}" type="button">Save</button>
          <button class="button danger" data-delete-item="${item.id}" type="button">Delete</button>
        </div>
          </div>
        </div>
      </article>
    `).join("") || `<p class="helper-text">No menu items yet.</p>`;
  }

  function collectRow(row) {
    return {
      name: row.querySelector('[name="name"]').value,
      description: row.querySelector('[name="description"]').value,
      price: row.querySelector('[name="price"]').value,
      category_id: row.querySelector('[name="category_id"]').value,
      tags: row.querySelector('[name="tags"]').value,
      is_available: row.querySelector('[name="is_available"]').checked,
      is_veg: row.querySelector('[name="is_veg"]').checked,
      is_bestseller: row.querySelector('[name="is_bestseller"]').checked,
    };
  }

  itemForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(itemForm);
    await apiFetch("/api/v1/admin/menu-items", {
      method: "POST",
      body: {
        category_id: form.get("category_id"),
        name: form.get("name"),
        price: form.get("price"),
        description: form.get("description"),
        tags: form.get("tags"),
        is_veg: form.get("is_veg") === "on",
        is_bestseller: form.get("is_bestseller") === "on",
        is_available: form.get("is_available") === "on",
      },
    });
    itemForm.reset();
    await load();
  });

  categoryForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(categoryForm);
    await apiFetch("/api/v1/admin/categories", {
      method: "POST",
      body: {
        name: form.get("name"),
        display_order: form.get("display_order"),
      },
    });
    categoryForm.reset();
    await load();
  });

  list.addEventListener("click", async (event) => {
    const save = event.target.closest("[data-save-item]");
    const del = event.target.closest("[data-delete-item]");
    if (save) {
      const row = save.closest(".admin-row");
      const itemId = save.dataset.saveItem;
      await apiFetch(`/api/v1/admin/menu-items/${itemId}`, {
        method: "PATCH",
        body: collectRow(row),
      });
      const image = row.querySelector('[name="image"]').files[0];
      if (image) {
        const form = new FormData();
        form.append("image", image);
        await apiFetch(`/api/v1/admin/menu-items/${itemId}/image`, {
          method: "POST",
          body: form,
        });
      }
      await load();
    }
    if (del && window.confirm("Delete this menu item?")) {
      await apiFetch(`/api/v1/admin/menu-items/${del.dataset.deleteItem}`, { method: "DELETE" });
      await load();
    }
  });

  list.addEventListener("change", (event) => {
    const input = event.target.closest('input[name="image"]');
    if (!input?.files?.[0]) return;
    const row = input.closest(".admin-row");
    const preview = row?.querySelector(".admin-menu-thumb");
    if (!preview) return;
    preview.src = URL.createObjectURL(input.files[0]);
  });

  searchInput?.addEventListener("input", render);
  categoryFilter?.addEventListener("change", render);
  refreshButton.addEventListener("click", load);
  load().catch((error) => {
    list.innerHTML = `<p class="helper-text">${escapeHtml(error.message)}</p>`;
  });
}

function initAdminTables() {
  const list = document.getElementById("tablesList");
  if (!list) return;
  const form = document.getElementById("tableForm");
  const printAllButton = document.getElementById("tablesPrintAll");
  let tableRows = [];

  function qrImageUrl(value, size = 260) {
    return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&margin=14&format=png&data=${encodeURIComponent(value)}`;
  }

  function posterSvg(table) {
    const menuUrl = `${window.location.origin}${table.menu_url}`;
    const logoUrl = `${window.location.origin}/static/brand/tea_trust_logo.png`;
    const qrUrl = qrImageUrl(menuUrl, 520);
    return `
      <svg xmlns="http://www.w3.org/2000/svg" width="900" height="1200" viewBox="0 0 900 1200">
        <rect width="900" height="1200" fill="#f6f8f7"/>
        <rect x="44" y="44" width="812" height="1112" rx="34" fill="#ffffff" stroke="#dce4e8" stroke-width="4"/>
        <rect x="44" y="44" width="812" height="310" rx="34" fill="#1f7a5c"/>
        <circle cx="450" cy="166" r="88" fill="#000000" stroke="#ffffff" stroke-width="10"/>
        <image href="${escapeHtml(logoUrl)}" x="367" y="83" width="166" height="166" preserveAspectRatio="xMidYMid slice"/>
        <text x="450" y="292" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="48" font-weight="900" fill="#ffffff">${escapeHtml(cafeName)}</text>
        <text x="450" y="420" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="38" font-weight="900" fill="#c85f28">SCAN TO ORDER</text>
        <text x="450" y="490" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="76" font-weight="900" fill="#1d2328">${escapeHtml(table.label)}</text>
        <rect x="185" y="545" width="530" height="530" rx="26" fill="#ffffff" stroke="#dce4e8" stroke-width="4"/>
        <image href="${escapeHtml(qrUrl)}" x="215" y="575" width="470" height="470"/>
        <text x="450" y="1110" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="26" font-weight="800" fill="#65717b">Open camera, scan, and place your order</text>
        <text x="450" y="1146" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="18" fill="#65717b">${escapeHtml(menuUrl)}</text>
      </svg>
    `.trim();
  }

  function posterPreviewHtml(table, qrUrl) {
    return `
      <div class="qr-poster-preview">
        <div class="poster-brand">
          <img src="/static/brand/tea_trust_logo.png" alt="" aria-hidden="true">
          <strong>${escapeHtml(cafeName)}</strong>
        </div>
        <span>Scan to order</span>
        <h3>${escapeHtml(table.label)}</h3>
        <img class="poster-qr" src="${escapeHtml(qrUrl)}" alt="QR code for ${escapeHtml(table.label)}" loading="lazy">
        <small>Camera scan menu</small>
      </div>
    `;
  }

  function downloadPoster(table) {
    const blob = new Blob([posterSvg(table)], { type: "image/svg+xml" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `tea-trust-${table.qr_slug}-poster.svg`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  function tableCardHtml(table) {
    const menuUrl = `${window.location.origin}${table.menu_url}`;
    const qrUrl = qrImageUrl(menuUrl);
    return `
      <article class="admin-row table-qr-row">
        <div class="qr-preview">
          ${posterPreviewHtml(table, qrUrl)}
        </div>
        <div class="table-qr-main">
          <header>
            <div>
              <strong>${escapeHtml(table.label)}</strong>
              <p class="helper-text">ID ${table.id} - ${escapeHtml(table.qr_slug)}</p>
            </div>
            <span class="status-pill">${table.is_active ? "active" : "inactive"}</span>
          </header>
          <input readonly value="${escapeHtml(menuUrl)}" aria-label="QR menu URL">
          <div class="row-actions">
            <a class="button mini-button" href="${escapeHtml(qrUrl)}" download="tea-trust-${escapeHtml(table.qr_slug)}.png">Download QR</a>
            <button class="button mini-button" data-download-poster="${table.id}" type="button">Download poster</button>
            <button class="button mini-button" data-print-qr="${table.id}" type="button">Print poster</button>
            <button class="button mini-button" data-copy-table-url="${table.id}" type="button">Copy link</button>
          </div>
        </div>
      </article>
    `;
  }

  function printTables(tables) {
    const content = tables.map((table) => {
      const menuUrl = `${window.location.origin}${table.menu_url}`;
      return `
        <section class="print-qr-card">
          <div class="print-head">
            <img class="print-logo" src="/static/brand/tea_trust_logo.png" alt="">
            <strong>${escapeHtml(cafeName)}</strong>
          </div>
          <p class="print-kicker">Scan to order</p>
          <h1>${escapeHtml(table.label)}</h1>
          <img class="print-qr" src="${escapeHtml(qrImageUrl(menuUrl, 420))}" alt="">
          <p class="print-help">Open camera, scan, and place your order</p>
          <small>${escapeHtml(menuUrl)}</small>
        </section>
      `;
    }).join("");
    const printWindow = window.open("", "qr-print");
    if (!printWindow) return;
    printWindow.document.write(`
      <!doctype html>
      <title>Table QR Codes</title>
      <style>
        body { background: #f6f8f7; font-family: Arial, sans-serif; margin: 0; padding: 24px; }
        .print-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }
        .print-qr-card { break-inside: avoid; border: 3px solid #dce4e8; border-radius: 24px; background: #fff; padding: 30px; text-align: center; }
        .print-head { display: grid; justify-items: center; gap: 10px; margin-bottom: 18px; }
        .print-logo { width: 92px; height: 92px; border-radius: 999px; object-fit: cover; background: #000; }
        .print-head strong { color: #1d2328; font-size: 24px; }
        .print-kicker { margin: 0 0 8px; color: #c85f28; font-size: 22px; font-weight: 900; text-transform: uppercase; }
        .print-qr-card h1 { margin: 0 0 18px; color: #1f7a5c; font-size: 44px; line-height: 1; }
        .print-qr { width: 290px; height: 290px; border: 1px solid #dce4e8; border-radius: 18px; padding: 12px; }
        .print-help { margin: 16px 0 10px; color: #1d2328; font-size: 18px; font-weight: 800; }
        small { color: #65717b; overflow-wrap: anywhere; }
        @media print { body { background: #fff; padding: 0; } .print-grid { gap: 0; } .print-qr-card { min-height: 45vh; border-radius: 0; } }
      </style>
      <body><main class="print-grid">${content}</main></body>
    `);
    printWindow.document.close();
    printWindow.focus();
    window.setTimeout(() => printWindow.print(), 450);
  }

  async function load() {
    tableRows = await apiFetch("/api/v1/admin/tables");
    list.innerHTML = tableRows.map(tableCardHtml).join("") || `<p class="helper-text">No tables found.</p>`;
  }

  list.addEventListener("click", async (event) => {
    const printButton = event.target.closest("[data-print-qr]");
    const downloadButton = event.target.closest("[data-download-poster]");
    const copyButton = event.target.closest("[data-copy-table-url]");
    if (downloadButton) {
      const table = tableRows.find((candidate) => String(candidate.id) === String(downloadButton.dataset.downloadPoster));
      if (table) downloadPoster(table);
    }
    if (printButton) {
      const table = tableRows.find((candidate) => String(candidate.id) === String(printButton.dataset.printQr));
      if (table) printTables([table]);
    }
    if (copyButton) {
      const table = tableRows.find((candidate) => String(candidate.id) === String(copyButton.dataset.copyTableUrl));
      if (!table) return;
      await navigator.clipboard?.writeText(`${window.location.origin}${table.menu_url}`);
      copyButton.textContent = "Copied";
      window.setTimeout(() => { copyButton.textContent = "Copy link"; }, 1200);
    }
  });

  printAllButton?.addEventListener("click", () => printTables(tableRows));

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    await apiFetch("/api/v1/admin/tables", {
      method: "POST",
      body: {
        table_number: data.get("table_number"),
        label: data.get("label"),
      },
    });
    form.reset();
    await load();
  });

  load().catch((error) => {
    list.innerHTML = `<p class="helper-text">${escapeHtml(error.message)}</p>`;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  if (pageId === "customer-menu") initCustomerMenu();
  if (pageId === "customer-cart" || pageId === "customer-checkout") initCustomerCartPage();
  if (pageId === "order-status") initOrderStatus();
  if (pageId === "admin-dashboard") initAdminDashboard();
  if (pageId === "admin-kitchen") initKitchenDisplay();
  if (pageId === "admin-analytics") initAdminAnalytics();
  if (pageId === "admin-menu") initAdminMenu();
  if (pageId === "admin-tables") initAdminTables();
});
