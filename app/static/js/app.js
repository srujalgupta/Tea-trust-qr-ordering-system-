const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
const pageId = document.body.dataset.page || "";
const cafeName = document.body.dataset.cafeName?.trim()
  || document.querySelector(".brand strong, .admin-brand strong")?.textContent?.trim()
  || "Tea Trust Cafe";
const currentOrderBaseKey = "qrCafeCurrentOrder";
const adminStoreKey = "qrCafeAdminStoreId";
const storeOptions = (() => {
  try {
    return JSON.parse(document.getElementById("storeOptionsJson")?.textContent || "[]");
  } catch {
    return [];
  }
})();
const bodyStore = {
  id: document.body.dataset.storeId || "",
  slug: document.body.dataset.storeSlug || "",
};

function storeById(storeId) {
  return storeOptions.find((store) => String(store.id) === String(storeId));
}

function storeBySlug(storeSlug) {
  return storeOptions.find((store) => String(store.slug) === String(storeSlug));
}

function selectedStore() {
  const currentPageStore = storeById(bodyStore.id) || storeBySlug(bodyStore.slug);
  if (currentPageStore) return currentPageStore;

  const isAdminPage = pageId.startsWith("admin-");
  if (isAdminPage) {
    const saved = localStorage.getItem(adminStoreKey);
    const savedStore = storeById(saved);
    if (savedStore) return savedStore;
  }
  return storeById(bodyStore.id) || storeBySlug(bodyStore.slug) || storeOptions[0] || null;
}

function selectedStoreId() {
  return selectedStore()?.id || bodyStore.id || "";
}

function selectedStoreSlug() {
  return selectedStore()?.slug || bodyStore.slug || "";
}

function selectedStoreName() {
  return selectedStore()?.name || "Store";
}

function scopedStorageKey(baseKey) {
  return `${baseKey}:${selectedStoreId() || selectedStoreSlug() || "default"}`;
}

function urlWithStore(path, options = {}) {
  const url = new URL(path, window.location.origin);
  const storeRef = options.store || selectedStoreSlug() || selectedStoreId();
  if (storeRef) {
    url.searchParams.set("store", storeRef);
  }
  if (options.tableId) {
    url.searchParams.set("table", options.tableId);
  }
  return `${url.pathname}${url.search}`;
}

function setupStoreSelector() {
  document.querySelectorAll("[data-store-select]").forEach((select) => {
    const mode = select.dataset.storeSelect;
    const active = selectedStore();
    if (active) {
      select.value = String(active.id);
    }

    select.addEventListener("change", () => {
      const option = select.selectedOptions[0];
      const storeId = select.value;
      const storeSlug = option?.dataset.slug || storeById(storeId)?.slug || "";
      if (mode === "admin") {
        localStorage.setItem(adminStoreKey, storeId);
        const nextUrl = new URL(window.location.href);
        if (storeSlug) {
          nextUrl.searchParams.set("store", storeSlug);
        } else {
          nextUrl.searchParams.set("store", storeId);
        }
        window.location.href = `${nextUrl.pathname}${nextUrl.search}`;
        return;
      }
      const nextUrl = new URL(window.location.href);
      if (storeSlug) {
        nextUrl.searchParams.set("store", storeSlug);
      }
      nextUrl.searchParams.delete("table");
      window.location.href = `${nextUrl.pathname}${nextUrl.search}`;
    });
  });

  document.querySelectorAll("[data-storefront-link]").forEach((link) => {
    link.href = urlWithStore("/menu");
  });
}

function filenamePart(value) {
  return String(value || "qr-cafe")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    || "qr-cafe";
}

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

function cssUrl(value) {
  const escaped = String(value || "")
    .replace(/[\n\r\f]/g, "")
    .replaceAll("\\", "\\\\")
    .replaceAll('"', '\\"');
  return `url("${escaped}")`;
}

function orderStatusUrl(order) {
  const id = order?.id;
  const key = order?.order_number || order?.orderKey || order?.key;
  if (!id || !key) return "";
  return `/order/${encodeURIComponent(id)}?key=${encodeURIComponent(key)}`;
}

function orderApiUrl(order) {
  const id = order?.id;
  const key = order?.order_number || order?.orderKey || order?.key;
  if (!id || !key) return "";
  return `/api/v1/orders/${encodeURIComponent(id)}?key=${encodeURIComponent(key)}`;
}

function currentOrderKeyFor(storeId = selectedStoreId()) {
  return `${currentOrderBaseKey}:${storeId || "default"}`;
}

function readCurrentOrder() {
  try {
    const order = JSON.parse(localStorage.getItem(currentOrderKeyFor()) || "null");
    if (!orderStatusUrl(order)) return null;
    return order;
  } catch {
    localStorage.removeItem(currentOrderKeyFor());
    return null;
  }
}

function saveCurrentOrder(order) {
  const id = order?.id;
  const orderNumber = order?.order_number || order?.orderKey || order?.key;
  if (!id || !orderNumber) return;
  const storeId = order.store_id ?? order.storeId ?? selectedStoreId() ?? "";
  localStorage.setItem(currentOrderKeyFor(storeId), JSON.stringify({
    id,
    order_number: orderNumber,
    store_id: storeId,
    table_id: order.table_id ?? order.tableId ?? null,
    table_label: order.table_label || "",
    status: order.status || "pending",
    token_number: order.token_number ?? null,
    total_amount: Number(order.total_amount || 0),
    created_at: order.created_at || "",
    saved_at: new Date().toISOString(),
  }));
}

function clearCurrentOrder() {
  localStorage.removeItem(currentOrderKeyFor());
}

function currentOrderActionLabel(order) {
  if (order?.status === "completed") return "View last bill";
  if (order?.status === "cancelled") return "View cancelled order";
  return "Track current order";
}

function currentOrderBelongsToTable(order, tableId, storeId = selectedStoreId()) {
  if (storeId && order?.store_id && String(order.store_id) !== String(storeId)) return false;
  if (!tableId || !order?.table_id) return true;
  return String(order.table_id) === String(tableId);
}

function setupCurrentOrderLinks(linkIds, tableId = null, storeId = selectedStoreId()) {
  const links = linkIds.map((id) => document.getElementById(id)).filter(Boolean);
  if (!links.length) return;

  function render(order) {
    const href = order && currentOrderBelongsToTable(order, tableId, storeId) ? orderStatusUrl(order) : "";
    links.forEach((link) => {
      if (!href) {
        link.hidden = true;
        link.removeAttribute("href");
        return;
      }
      link.hidden = false;
      link.href = href;
      link.textContent = currentOrderActionLabel(order);
      link.setAttribute("aria-label", `${currentOrderActionLabel(order)} ${order.order_number}`);
    });
  }

  const storedOrder = readCurrentOrder();
  render(storedOrder);
  if (!storedOrder) return;

  apiFetch(orderApiUrl(storedOrder)).then((order) => {
    saveCurrentOrder(order);
    render(order);
  }).catch(() => {
    clearCurrentOrder();
    render(null);
  });
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

function unsplashPhoto(photoId) {
  return `https://images.unsplash.com/${photoId}?auto=format&fit=crop&w=900&q=80`;
}

const REAL_FOOD_PHOTOS = [
  {
    test: /(masala|ginger|elaichi|pudina|tulasi|tulsi|cinnamon|kesar).*tea|tea with milk|chai/i,
    url: unsplashPhoto("photo-1625033405953-f20401c7d848"),
  },
  {
    test: /(black lemon|darjeeling|green lemon|organic tulsi|lemon tea|green tea|tea without milk)/i,
    url: unsplashPhoto("photo-1758705206938-a196ac3ae3bb"),
  },
  {
    test: /(ice tea|iced tea|fresh lime|lime water|peach|muskmelon|mixed berries)/i,
    url: unsplashPhoto("photo-1758705206938-a196ac3ae3bb"),
  },
  {
    test: /(cold coffee|iced coffee|black iced coffee|choco fiesta)/i,
    url: unsplashPhoto("photo-1770299258214-1b7bc604e3fd"),
  },
  {
    test: /(hot chocolate|bournvita|kesar masala milk|milk)/i,
    url: unsplashPhoto("photo-1542990253-0d0f5be5f0ed"),
  },
  {
    test: /(coffee)/i,
    url: unsplashPhoto("photo-1509042239860-f550ce710b93"),
  },
  {
    test: /(garlic bread|chilly cheese|corn cheese|veg\.? supreme|open toast)/i,
    url: unsplashPhoto("photo-1761321982794-6165b979f511"),
  },
  {
    test: /(bread butter|bread butter jam|toast|khari|bun|maska)/i,
    url: unsplashPhoto("photo-1509440159596-0249088772ff"),
  },
  {
    test: /(khakhra|bhakhri|thepla|flatbread|kathiyawadi)/i,
    url: unsplashPhoto("photo-1767114915936-745dd372f1d8"),
  },
  {
    test: /(chocolate sandwich)/i,
    url: unsplashPhoto("photo-1578985545062-69928b1d9587"),
  },
  {
    test: /(sandwich|club|coleslow|chutney|paneer sandwich|mexican|maxican|heritage)/i,
    url: unsplashPhoto("photo-1528735602780-2552fd46c7af"),
  },
  {
    test: /(vada pav|paneer tandoori burger|burger)/i,
    url: unsplashPhoto("photo-1568901346375-23c9450c58cd"),
  },
  {
    test: /(fries|wedges|nuggets|crispers|shotz|shots|fingers|popcorn|smiles|triangle|potato balls|v crispers)/i,
    url: unsplashPhoto("photo-1573080496219-bb080dd4f877"),
  },
  {
    test: /(blue curacao)/i,
    url: unsplashPhoto("photo-1746950523046-a4db7f176e3d"),
  },
  {
    test: /(mojito|mint|green apple mocktail)/i,
    url: unsplashPhoto("photo-1603064752734-4c48eff53d05"),
  },
  {
    test: /(mocktail|pomegranate mocktail|blackcurrant mocktail|black current mocktail)/i,
    url: unsplashPhoto("photo-1536935338788-846bb9981813"),
  },
  {
    test: /(oreo|kit kat|snickers|five star|caramel chocolate|chocolate shake)/i,
    url: unsplashPhoto("photo-1761655439819-458513191d74"),
  },
  {
    test: /(shake|vanilla|strawberry|banana|lychee|kiwi|guava|pineapple|blueberry|blue berry|caramel)/i,
    url: unsplashPhoto("photo-1572490122747-3968b75cc699"),
  },
  {
    test: /(cheese veg\.? maggi|maggi|noodles)/i,
    url: unsplashPhoto("photo-1692273212247-f5efb3fc9b87"),
  },
  {
    test: /(cheese|paneer add-on|paneer add on)/i,
    url: unsplashPhoto("photo-1486297678162-eb2a19b0a32d"),
  },
  {
    test: /(honey add-on|honey add on|honey)/i,
    url: unsplashPhoto("photo-1587049352846-4a222e784d38"),
  },
  {
    test: /(chocolate sauce add-on|chocolate sauce add on|chocolate sauce)/i,
    url: unsplashPhoto("photo-1606313564200-e75d5e30476c"),
  },
];

function realFoodPhoto(item) {
  const text = `${item.category_name || ""} ${item.name || ""} ${(item.tags || []).join(" ")}`;
  const match = REAL_FOOD_PHOTOS.find((photo) => photo.test.test(text));
  return match?.url || unsplashPhoto("photo-1543352634-a1c51d9f1fa7");
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
    ".button, .icon-button, .chip, .customer-action-button, .floating-cart-button, .admin-nav-link, .delivery-app-button, .menu-section-toggle, .stepper button",
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

  if (hero.dataset.posterUrl) {
    hero.style.setProperty("--poster", cssUrl(hero.dataset.posterUrl));
  }

  const storeId = hero.dataset.storeId || selectedStoreId();
  const storeSlug = hero.dataset.storeSlug || selectedStoreSlug();
  const tableId = hero.dataset.tableId || null;
  const menuList = document.getElementById("menuList");
  const searchInput = document.getElementById("menuSearch");
  const categoryTabs = document.getElementById("categoryTabs");
  const cartShortcutButton = document.getElementById("cartShortcut");
  const checkoutShortcutButton = document.getElementById("checkoutShortcut");
  const mobileCartShortcutButton = document.getElementById("mobileCartShortcut");
  const mobileCheckoutShortcutButton = document.getElementById("mobileCheckoutShortcut");
  const floatingCartShortcutButton = document.getElementById("floatingCartShortcut");
  const cartCountEls = [
    document.getElementById("cartItemCount"),
    document.getElementById("mobileCartItemCount"),
    document.getElementById("floatingCartItemCount"),
  ].filter(Boolean);
  const checkoutAmountEls = [
    document.getElementById("checkoutAmount"),
    document.getElementById("mobileCheckoutAmount"),
    document.getElementById("floatingCartAmount"),
  ].filter(Boolean);
  const menuItemTotalEl = document.getElementById("menuItemTotal");
  const bestsellerTotalEl = document.getElementById("bestsellerTotal");
  const cartKey = scopedStorageKey("qrCafeCart");
  const tableKey = scopedStorageKey("qrCafeTableId");

  let categories = [];
  let items = [];
  let menuEntries = [];
  let openCategories = new Set();
  let cart = JSON.parse(localStorage.getItem(cartKey) || "{}");
  let selectedVariantByEntry = {};

  if (tableId) {
    localStorage.setItem(tableKey, tableId);
  }
  setupCurrentOrderLinks(["menuCurrentOrderLink"], tableId || localStorage.getItem(tableKey) || null, storeId);

  function saveCart() {
    localStorage.setItem(cartKey, JSON.stringify(cart));
  }

  function normalizedMenuKey(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function parseVariantName(name) {
    const match = String(name || "").match(/^(.+?)\s*\(([^)]+)\)\s*$/);
    if (!match) {
      return {
        baseName: String(name || "").trim(),
        variantLabel: "Regular",
        hasVariant: false,
      };
    }
    return {
      baseName: match[1].trim(),
      variantLabel: match[2].trim(),
      hasVariant: true,
    };
  }

  function variantSortRank(label) {
    const normalized = normalizedMenuKey(label);
    const preferredOrder = ["quarter", "half", "small", "regular", "medium", "full", "large", "plain", "grilled"];
    const index = preferredOrder.indexOf(normalized);
    return index === -1 ? preferredOrder.length : index;
  }

  function uniqueTagsForVariants(variants) {
    const seen = new Set();
    const variantLabels = new Set(variants.map((variant) => normalizedMenuKey(variant.variantLabel)));
    variants.forEach((variant) => {
      (variant.tags || []).forEach((tag) => {
        const normalized = normalizedMenuKey(tag);
        if (!normalized || ["veg", "bestseller"].includes(normalized) || variantLabels.has(normalized)) return;
        seen.add(tag);
      });
    });
    return [...seen];
  }

  function menuEntryFromGroup(group) {
    const variants = group.rows
      .map(({ item, parsed }) => ({
        ...item,
        variantLabel: parsed.variantLabel,
      }))
      .sort((first, second) => (
        variantSortRank(first.variantLabel) - variantSortRank(second.variantLabel)
        || Number(first.price || 0) - Number(second.price || 0)
        || String(first.name).localeCompare(String(second.name))
      ));
    const primary = variants.find((variant) => variant.image_url) || variants[0];
    const entryKey = group.rows.length > 1
      ? `group-${primary.category_id}-${normalizedMenuKey(group.baseName)}`
      : `item-${primary.id}`;
    const entryName = group.rows.length > 1 ? group.baseName : primary.name;
    const searchText = [
      entryName,
      primary.category_name,
      ...variants.flatMap((variant) => [
        variant.name,
        variant.variantLabel,
        variant.description,
        ...(variant.tags || []),
      ]),
    ].join(" ").toLowerCase();

    return {
      key: entryKey,
      category_id: primary.category_id,
      category_name: primary.category_name,
      name: entryName,
      description: variants.find((variant) => variant.description)?.description || "",
      image_url: primary.image_url || "",
      is_veg: variants.every((variant) => variant.is_veg),
      is_bestseller: variants.some((variant) => variant.is_bestseller),
      tags: uniqueTagsForVariants(variants),
      variants,
      searchText,
      firstIndex: group.firstIndex,
    };
  }

  function rebuildMenuEntries() {
    const variantGroups = new Map();
    const directGroups = [];
    items.forEach((item, index) => {
      const parsed = parseVariantName(item.name);
      if (!parsed.hasVariant) {
        directGroups.push({
          baseName: item.name,
          rows: [{ item, parsed }],
          firstIndex: index,
        });
        return;
      }
      const key = `${item.category_id}:${normalizedMenuKey(parsed.baseName)}`;
      const group = variantGroups.get(key) || {
        baseName: parsed.baseName,
        rows: [],
        firstIndex: index,
      };
      group.rows.push({ item, parsed });
      group.firstIndex = Math.min(group.firstIndex, index);
      variantGroups.set(key, group);
    });

    const groupedEntries = [...variantGroups.values()].flatMap((group) => {
      if (group.rows.length > 1) return [menuEntryFromGroup(group)];
      return group.rows.map(({ item, parsed }) => menuEntryFromGroup({
        baseName: item.name,
        rows: [{ item, parsed: { ...parsed, variantLabel: "Regular" } }],
        firstIndex: group.firstIndex,
      }));
    });

    menuEntries = [...groupedEntries, ...directGroups.map(menuEntryFromGroup)]
      .sort((first, second) => first.firstIndex - second.firstIndex);
  }

  function itemsForCategory(categoryId) {
    const q = searchInput.value.trim().toLowerCase();
    return menuEntries.filter((entry) => {
      const inCategory = String(entry.category_id) === String(categoryId);
      return inCategory && (!q || entry.searchText.includes(q));
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
    const savedTableId = tableId || localStorage.getItem(tableKey) || "";
    return urlWithStore(path, { store: storeSlug || storeId, tableId: savedTableId });
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
        <button class="category-tab ${openCategories.has(categoryId) ? "active" : ""}" data-category-tab="${category.id}" type="button" aria-pressed="${openCategories.has(categoryId)}">
          <span>${escapeHtml(category.name)}</span>
          <small>${count}</small>
        </button>
      `;
    }).join("");
  }

  function renderMenuStats() {
    const bestsellerCount = menuEntries.filter((entry) => entry.is_bestseller).length;
    if (menuItemTotalEl) {
      menuItemTotalEl.textContent = `${menuEntries.length} product${menuEntries.length === 1 ? "" : "s"}`;
    }
    if (bestsellerTotalEl) {
      bestsellerTotalEl.textContent = `${bestsellerCount} pick${bestsellerCount === 1 ? "" : "s"}`;
    }
  }

  function renderMenu() {
    function selectedVariantFor(entry) {
      const rememberedId = selectedVariantByEntry[entry.key];
      const rememberedVariant = entry.variants.find((variant) => String(variant.id) === String(rememberedId));
      if (rememberedVariant) return rememberedVariant;
      const cartVariant = entry.variants.find((variant) => Number(cart[variant.id] || 0) > 0);
      const selectedVariant = cartVariant || entry.variants[0];
      selectedVariantByEntry[entry.key] = String(selectedVariant.id);
      return selectedVariant;
    }

    function priceLabel(entry, selectedVariant) {
      if (entry.variants.length < 2) return money(selectedVariant.price);
      const prices = entry.variants.map((variant) => Number(variant.price || 0));
      const minPrice = Math.min(...prices);
      const maxPrice = Math.max(...prices);
      return minPrice === maxPrice ? money(minPrice) : `${money(minPrice)} - ${money(maxPrice)}`;
    }

    function itemCard(entry) {
      const selectedVariant = selectedVariantFor(entry);
      const quantity = Number(cart[selectedVariant.id] || 0);
      const totalQuantity = entry.variants.reduce((total, variant) => total + Number(cart[variant.id] || 0), 0);
      const hasVariants = entry.variants.length > 1;
      const tags = (entry.tags || [])
        .filter((tag) => !["veg", "bestseller"].includes(String(tag).toLowerCase()))
        .map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`)
        .join("");
      const variantField = hasVariants
        ? `<label class="item-variant-field">
            <span>Size</span>
            <select data-menu-variant="${escapeHtml(entry.key)}" aria-label="Choose size for ${escapeHtml(entry.name)}">
              ${entry.variants.map((variant) => `
                <option value="${variant.id}" ${String(variant.id) === String(selectedVariant.id) ? "selected" : ""}>
                  ${escapeHtml(variant.variantLabel)} - ${money(variant.price)}
                </option>
              `).join("")}
            </select>
          </label>`
        : "";
      const cartPill = totalQuantity && !quantity
        ? `<span class="in-cart-pill">${totalQuantity} in cart</span>`
        : "";
      const itemAction = quantity
        ? `<div class="item-card-actions has-quantity">
            <div class="menu-item-stepper stepper" aria-label="Quantity for ${escapeHtml(selectedVariant.name)}">
              <button type="button" data-menu-step="${selectedVariant.id}" data-delta="-1">-</button>
              <span>${quantity}</span>
              <button type="button" data-add="${selectedVariant.id}">+</button>
            </div>
            <span class="in-cart-pill">In cart</span>
          </div>`
        : `<div class="item-card-actions">
            <button class="button primary full-width" data-add="${selectedVariant.id}" type="button">${hasVariants ? `Add ${escapeHtml(selectedVariant.variantLabel)}` : "Add to cart"}</button>
            ${cartPill}
          </div>`;
      return `
        <article class="item-card">
          ${imageTag(entry)}
          <div class="item-body">
            <div class="item-title">
              <h3>${escapeHtml(entry.name)}</h3>
              <span class="price">${priceLabel(entry, selectedVariant)}</span>
            </div>
            <div class="item-meta-row">
              <span class="veg-indicator ${entry.is_veg ? "is-veg" : "is-non-veg"}">
                <span aria-hidden="true"></span>${entry.is_veg ? "Veg" : "Non-veg"}
              </span>
              ${entry.is_bestseller ? `<span class="bestseller-chip">Popular</span>` : ""}
            </div>
            <p>${escapeHtml(entry.description)}</p>
            ${tags ? `<div class="tag-row">${tags}</div>` : ""}
            ${variantField}
            ${itemAction}
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
              <span class="menu-count">${categoryItems.length} product${categoryItems.length === 1 ? "" : "s"}</span>
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
    renderMenuStats();
    renderCategoryTabs();
    renderMenu();
    renderCartSummary();
  }

  async function loadMenu() {
    const payload = await apiFetch(urlWithStore("/api/v1/menu", { store: storeSlug || storeId }));
    categories = payload.categories;
    items = payload.items;
    rebuildMenuEntries();
    if (!openCategories.size) {
      const firstCategory = categories.find((category) => (
        menuEntries.some((entry) => String(entry.category_id) === String(category.id))
      ));
      if (firstCategory) {
        openCategories.add(String(firstCategory.id));
      }
    }
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

    const stepButton = event.target.closest("[data-menu-step]");
    if (stepButton) {
      const id = stepButton.dataset.menuStep;
      cart[id] = (cart[id] || 0) + Number(stepButton.dataset.delta);
      if (cart[id] <= 0) {
        delete cart[id];
      }
      saveCart();
      renderAll();
      return;
    }

    const button = event.target.closest("[data-add]");
    if (!button) return;
    const id = button.dataset.add;
    cart[id] = (cart[id] || 0) + 1;
    saveCart();
    renderAll();
  });

  menuList.addEventListener("change", (event) => {
    const variantSelect = event.target.closest("[data-menu-variant]");
    if (!variantSelect) return;
    selectedVariantByEntry[variantSelect.dataset.menuVariant] = variantSelect.value;
    renderAll();
  });

  cartShortcutButton?.addEventListener("click", () => goToCustomerPage("/cart"));
  mobileCartShortcutButton?.addEventListener("click", () => goToCustomerPage("/cart"));
  floatingCartShortcutButton?.addEventListener("click", () => goToCustomerPage("/cart"));
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

  const storeId = shell.dataset.storeId || selectedStoreId();
  const storeSlug = shell.dataset.storeSlug || selectedStoreSlug();
  const cartKey = scopedStorageKey("qrCafeCart");
  const tableKey = scopedStorageKey("qrCafeTableId");
  const customerKey = "qrCafeCustomer";
  const itemNotesKey = scopedStorageKey("qrCafeItemNotes");
  const cartItemsEl = document.getElementById("cartItems");
  const cartItemSummaryEl = document.getElementById("cartItemSummary");
  const cartSubtotalEl = document.getElementById("cartSubtotal");
  const cartTotalEl = document.getElementById("cartTotal");
  const cartMessage = document.getElementById("cartMessage");
  const waitEstimateEls = [
    document.getElementById("cartWaitEstimate"),
    document.getElementById("checkoutWaitEstimate"),
  ].filter(Boolean);
  const clearCartButton = document.getElementById("clearCart");
  const checkoutPageButton = document.getElementById("checkoutPageButton");
  const placeOrderButton = document.getElementById("placeOrder");
  const checkoutMode = shell.dataset.mode === "checkout";
  let tableId = shell.dataset.tableId || localStorage.getItem(tableKey) || null;
  let items = [];
  let cart = JSON.parse(localStorage.getItem(cartKey) || "{}");
  let itemNotes = JSON.parse(localStorage.getItem(itemNotesKey) || "{}");
  let waitEstimateTimer = null;
  let waitEstimateRequestId = 0;

  if (shell.dataset.tableId) {
    localStorage.setItem(tableKey, shell.dataset.tableId);
    tableId = shell.dataset.tableId;
  }
  setupCurrentOrderLinks(["cartCurrentOrderLink"], tableId, storeId);

  function customerPageUrl(path) {
    return urlWithStore(path, { store: storeSlug || storeId, tableId });
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

  function cartEstimateItems() {
    return Object.entries(cart)
      .filter(([id, quantity]) => quantity > 0 && items.some((item) => String(item.id) === String(id)))
      .map(([menu_item_id, quantity]) => ({
        menu_item_id: Number(menu_item_id),
        quantity,
      }));
  }

  function setWaitEstimateText(text) {
    waitEstimateEls.forEach((element) => {
      element.textContent = text;
    });
  }

  function scheduleWaitEstimate() {
    if (!waitEstimateEls.length) return;
    window.clearTimeout(waitEstimateTimer);
    waitEstimateRequestId += 1;
    const requestId = waitEstimateRequestId;
    const { count } = cartStats();
    if (!count) {
      setWaitEstimateText("Add items to see wait time");
      return;
    }

    setWaitEstimateText("Updating wait time...");
    waitEstimateTimer = window.setTimeout(async () => {
      try {
        const payload = await apiFetch("/api/v1/orders/wait-estimate", {
          method: "POST",
          body: {
            store_id: storeId,
            table_id: tableId,
            items: cartEstimateItems(),
          },
        });
        if (requestId !== waitEstimateRequestId) return;
        setWaitEstimateText(payload.estimated_wait_label || "Estimated wait updating");
      } catch {
        if (requestId === waitEstimateRequestId) {
          setWaitEstimateText("Wait time updates at checkout");
        }
      }
    }, 250);
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
    scheduleWaitEstimate();
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
      const customerName = document.getElementById("customerName").value;
      const customerPhone = document.getElementById("customerPhone").value;
      const marketingOptIn = document.getElementById("marketingOptIn")?.checked || false;
      localStorage.setItem(customerKey, JSON.stringify({
        name: customerName,
        phone: customerPhone,
        marketingOptIn,
      }));
      const order = await apiFetch("/api/v1/orders", {
        method: "POST",
        body: {
          table_id: tableId,
          store_id: storeId,
          customer_name: customerName,
          customer_phone: customerPhone,
          marketing_opt_in: marketingOptIn,
          notes: document.getElementById("orderNotes").value,
          payment_method: "cash",
          items: orderItems,
        },
      });

      cart = {};
      itemNotes = {};
      saveCart();
      saveItemNotes();
      saveCurrentOrder(order);
      window.location.href = orderStatusUrl(order);
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

  apiFetch(urlWithStore("/api/v1/menu", { store: storeSlug || storeId })).then((payload) => {
    items = payload.items;
    const savedCustomer = JSON.parse(localStorage.getItem(customerKey) || "{}");
    if (checkoutMode) {
      const nameField = document.getElementById("customerName");
      const phoneField = document.getElementById("customerPhone");
      const marketingField = document.getElementById("marketingOptIn");
      if (nameField && savedCustomer.name) nameField.value = savedCustomer.name;
      if (phoneField && savedCustomer.phone) phoneField.value = savedCustomer.phone;
      if (marketingField && savedCustomer.marketingOptIn) marketingField.checked = true;
    }
    renderCart();
    if (checkoutMode && cartStats().count) {
      window.setTimeout(() => document.getElementById("customerName")?.focus(), 250);
    }
  }).catch((error) => {
    cartItemsEl.innerHTML = `<p class="helper-text">${escapeHtml(error.message)}</p>`;
  });
}

function paymentLabel(order) {
  if (order.payment_method === "cash" && order.payment_status === "cash_pending") {
    return "Pay at store";
  }
  if (order.payment_method === "cash" && order.payment_status === "paid") {
    return "Paid at store";
  }
  return String(order.payment_status || "pending").replaceAll("_", " ");
}

function formatBillDate(value) {
  if (!value) return "Just now";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Just now";
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function receiptHtml(order, options = {}) {
  const billTitle = options.title || "Bill";
  const showCustomer = options.showCustomer || Boolean(order.customer_name || order.customer_phone);
  const lines = (order.items || []).map((item) => (
    `<div class="receipt-item">
      <span>${escapeHtml(item.item_name)} <small>x ${item.quantity}</small></span>
      <strong>${money(item.line_total)}</strong>
    </div>`
  )).join("");
  const customerRows = showCustomer
    ? `<p><strong>Customer</strong><span>${escapeHtml(order.customer_name || "Guest")}</span></p>
       <p><strong>Phone</strong><span>${escapeHtml(order.customer_phone || "Not shared")}</span></p>`
    : "";
  return `
    <section class="receipt-card">
      <header class="receipt-header">
        <div>
          <p class="eyebrow">${escapeHtml(billTitle)}</p>
          <h2>${escapeHtml(cafeName)}</h2>
          <span>Bill ${escapeHtml(order.order_number)}</span>
          <small>${escapeHtml(formatBillDate(order.created_at))}</small>
        </div>
        <strong>${order.token_number ? `Token ${order.token_number}` : "Token pending"}</strong>
      </header>
      <div class="order-detail-grid receipt-meta-grid">
        <p><strong>Status</strong><span>${escapeHtml(order.status.replaceAll("_", " "))}</span></p>
        <p><strong>Payment</strong><span>${escapeHtml(paymentLabel(order))}</span></p>
        <p><strong>Store</strong><span>${escapeHtml(order.store_name || selectedStoreName())}</span></p>
        <p><strong>Table</strong><span>${escapeHtml(order.table_label || "Takeaway")}</span></p>
        <p><strong>Total</strong><span>${money(order.total_amount)}</span></p>
        ${customerRows}
      </div>
      <div class="receipt-items">${lines}</div>
      <div class="receipt-lines receipt-total-lines">
        <div><span>Item subtotal</span><strong>${money(order.subtotal_amount)}</strong></div>
        <div><span>Taxes</span><strong>${money(order.tax_amount)}</strong></div>
        <div class="receipt-grand-total"><span>Total payable</span><strong>${money(order.total_amount)}</strong></div>
      </div>
      <p class="receipt-payment-note">${order.payment_status === "paid" ? "Payment received at store." : "Payment pending at the counter."}</p>
    </section>
  `;
}

function printBill(order) {
  const printWindow = window.open("", "order-bill");
  if (!printWindow) return;
  printWindow.document.write(`
    <!doctype html>
    <html>
      <head>
        <title>Bill ${escapeHtml(order.order_number)}</title>
        <style>
          * { box-sizing: border-box; }
          body { margin: 0; background: #f6f8f7; color: #1d2328; font-family: Arial, Helvetica, sans-serif; padding: 24px; }
          .receipt-card { max-width: 520px; margin: 0 auto; display: grid; gap: 14px; border: 1px solid #dce4e8; border-radius: 8px; background: #fff; padding: 18px; }
          .receipt-header { display: flex; justify-content: space-between; gap: 16px; border-bottom: 1px dashed #cbd7dc; padding-bottom: 12px; }
          .eyebrow { margin: 0 0 4px; color: #1f7a5c; font-size: 11px; font-weight: 900; letter-spacing: 0; text-transform: uppercase; }
          h2 { margin: 0 0 4px; font-size: 22px; }
          .receipt-header span, .receipt-header small { display: block; color: #65717b; font-weight: 800; }
          .receipt-header > strong { align-self: start; border-radius: 999px; background: #edf6f2; color: #1f7a5c; padding: 7px 10px; white-space: nowrap; }
          .order-detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
          .order-detail-grid p { min-height: 64px; display: grid; gap: 5px; margin: 0; border: 1px solid #dce4e8; border-radius: 8px; background: #f9fbfa; padding: 10px; }
          .order-detail-grid strong { color: #1d2328; }
          .order-detail-grid span { color: #65717b; text-transform: capitalize; overflow-wrap: anywhere; }
          .receipt-items { display: grid; gap: 9px; }
          .receipt-item, .receipt-lines div { display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px dashed #e3ebee; padding-bottom: 8px; }
          .receipt-item:last-child { border-bottom: 0; padding-bottom: 0; }
          .receipt-item small { color: #65717b; font-weight: 800; }
          .receipt-lines { display: grid; gap: 8px; border-top: 1px dashed #cbd7dc; padding-top: 10px; }
          .receipt-grand-total { border-top: 1px solid #dce4e8; margin-top: 4px; padding-top: 8px; font-size: 18px; font-weight: 900; }
          .receipt-payment-note { margin: 0; color: #65717b; }
          @media print { body { background: #fff; padding: 0; } .receipt-card { border: 0; max-width: none; } }
        </style>
      </head>
      <body>${receiptHtml(order, { title: "Bill", showCustomer: true })}</body>
    </html>
  `);
  printWindow.document.close();
  printWindow.focus();
  window.setTimeout(() => printWindow.print(), 350);
}

function orderDetailsHtml(order) {
  return receiptHtml(order, { title: "Bill", showCustomer: true });
}

function estimatedWaitLabel(order) {
  if (order.estimated_wait_label) return order.estimated_wait_label;
  if (order.status === "ready") return "Ready now";
  if (order.status === "completed") return "Completed";
  if (order.status === "cancelled") return "Order cancelled";
  if (order.status === "preparing") return "Estimated wait: 8-12 minutes";
  return "Estimated wait: 12-18 minutes";
}

function customerStatusLabel(status) {
  return String(status || "pending")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function whatsappConfirmationUrl(order) {
  const token = order.token_number ? `Token ${order.token_number}` : "Payment pending";
  const table = order.table_label ? `Table: ${order.table_label}` : "Order type: Takeaway";
  const items = order.items.map((item) => `${item.item_name} x ${item.quantity}`).join(", ");
  const message = [
    `${cafeName} order confirmation`,
    `Store: ${order.store_name || selectedStoreName()}`,
    `Order: ${order.order_number}`,
    token,
    table,
    `Items: ${items}`,
    `Total: ${money(order.total_amount)}`,
    "Payment: Pay at store",
  ].join("\n");
  return `https://wa.me/?text=${encodeURIComponent(message)}`;
}

function initOrderStatus() {
  const panel = document.querySelector(".token-panel");
  if (!panel) return;
  const orderId = panel.dataset.orderId;
  const orderKey = panel.dataset.orderKey || "";
  const tokenNumber = document.getElementById("tokenNumber");
  const tokenStatus = document.getElementById("tokenStatus");
  const details = document.getElementById("orderStatusDetails");
  const estimatedWait = document.getElementById("estimatedWait");
  const whatsAppLink = document.getElementById("whatsAppConfirmLink");
  const printBillButton = document.getElementById("printBillButton");
  const paymentNotice = document.getElementById("paymentNotice");
  const pollDelay = 2500;
  let isRefreshing = false;
  let currentOrder = null;

  saveCurrentOrder({
    id: orderId,
    order_number: orderKey,
    store_id: panel.dataset.storeId || selectedStoreId(),
    table_id: panel.dataset.tableId || null,
    status: "pending",
  });

  function render(order) {
    if (!order || String(order.id) !== String(orderId)) return;
    currentOrder = order;
    saveCurrentOrder(order);
    tokenNumber.textContent = order.token_number ? `Token ${order.token_number}` : "Payment pending";
    tokenStatus.textContent = customerStatusLabel(order.status);
    tokenStatus.className = `status-pill status-${order.status}`;
    estimatedWait.textContent = estimatedWaitLabel(order);
    if (paymentNotice) {
      paymentNotice.textContent = order.payment_status === "paid"
        ? "Payment received at store. Thank you."
        : "Pay at store. Please pay directly at the counter when collecting your order.";
    }
    whatsAppLink.href = whatsappConfirmationUrl(order);
    details.innerHTML = orderDetailsHtml(order);
  }

  printBillButton?.addEventListener("click", () => {
    if (currentOrder) printBill(currentOrder);
  });

  async function refresh() {
    if (isRefreshing) return;
    isRefreshing = true;
    try {
      const order = await apiFetch(`/api/v1/orders/${orderId}?key=${encodeURIComponent(orderKey)}`);
      render(order);
    } finally {
      isRefreshing = false;
    }
  }

  const socket = connectSocket();
  if (socket) {
    socket.on("connect", () => {
      socket.emit("customer_join", { order_id: orderId, order_key: orderKey });
      refresh().catch(() => {});
    });
    socket.io?.on("reconnect", () => {
      socket.emit("customer_join", { order_id: orderId, order_key: orderKey });
      refresh().catch(() => {});
    });
    socket.on("order_updated", render);
  }

  setInterval(() => {
    if (!document.hidden) refresh().catch(() => {});
  }, pollDelay);

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) refresh().catch(() => {});
  });

  refresh().catch(() => {});
}

function initAdminDashboard() {
  const board = document.getElementById("ordersBoard");
  if (!board) return;
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
  const printOrderBillButton = document.getElementById("printOrderBillButton");
  const counterOrderForm = document.getElementById("counterOrderForm");
  const counterTableSelect = document.getElementById("counterTableSelect");
  const counterCustomerName = document.getElementById("counterCustomerName");
  const counterCustomerPhone = document.getElementById("counterCustomerPhone");
  const counterItemSearch = document.getElementById("counterItemSearch");
  const counterItemSuggestions = document.getElementById("counterItemSuggestions");
  const counterItemSelect = document.getElementById("counterItemSelect");
  const counterItemQty = document.getElementById("counterItemQty");
  const counterAddItem = document.getElementById("counterAddItem");
  const counterOrderItems = document.getElementById("counterOrderItems");
  const counterOrderTotal = document.getElementById("counterOrderTotal");
  const counterOrderNotes = document.getElementById("counterOrderNotes");
  const counterOrderMessage = document.getElementById("counterOrderMessage");
  const statusValues = ["pending", "preparing", "ready", "completed", "cancelled"];
  const recentOrderLimit = 12;
  const activeStoreId = selectedStoreId();
  const seenOrdersKey = scopedStorageKey("qrCafeSeenOrders");
  let orders = [];
  let tables = [];
  let menuItems = [];
  let counterItems = [];
  let isLoading = false;
  let dashboardDataSignature = "";
  let seenOrderIds = new Set(JSON.parse(localStorage.getItem(seenOrdersKey) || "[]"));
  let alertsEnabled = localStorage.getItem("qrCafeAdminAlerts") === "on";
  let alertAudioContext = null;
  let alertToneTimer = null;
  let audioUnlocked = false;
  let hasLoadedDashboard = false;
  let knownOrderIds = new Set();
  let selectedOrder = null;
  let counterSuggestionIndex = 0;

  function supportsAlertAudio() {
    return Boolean(window.AudioContext || window.webkitAudioContext);
  }

  function renderAlertState() {
    if (!alertsButton || !alertsStatus) return;
    if (!alertsEnabled) {
      alertsButton.textContent = "Enable sound";
      alertsButton.classList.remove("primary");
      alertsStatus.textContent = "Sound alerts are off";
      return;
    }
    if (!supportsAlertAudio()) {
      alertsButton.textContent = "Sound unavailable";
      alertsButton.classList.remove("primary");
      alertsStatus.textContent = "This browser cannot play dashboard sounds";
      return;
    }
    alertsButton.textContent = audioUnlocked ? "Sound on" : "Arm sound";
    alertsButton.classList.toggle("primary", audioUnlocked);
    alertsStatus.textContent = audioUnlocked
      ? "Sound and desktop alerts are on"
      : "Tap Arm sound once to allow browser audio";
  }

  function ensureAlertAudio() {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return null;
    if (!alertAudioContext || alertAudioContext.state === "closed") {
      try {
        alertAudioContext = new AudioContext();
      } catch (error) {
        return null;
      }
    }
    audioUnlocked = alertAudioContext.state === "running";
    return alertAudioContext;
  }

  async function unlockAlertAudio() {
    const audio = ensureAlertAudio();
    if (!audio) {
      audioUnlocked = false;
      renderAlertState();
      return false;
    }
    try {
      if (audio.state === "suspended") {
        await audio.resume();
      }
    } catch (error) {
      audioUnlocked = false;
      renderAlertState();
      return false;
    }
    audioUnlocked = audio.state === "running";
    renderAlertState();
    return audioUnlocked;
  }

  function playKitchenTone() {
    if (!alertsEnabled) return false;
    const audio = ensureAlertAudio();
    if (!audio || audio.state !== "running") {
      audioUnlocked = false;
      renderAlertState();
      return false;
    }
    audioUnlocked = true;
    const start = audio.currentTime + 0.02;
    try {
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
      renderAlertState();
      return true;
    } catch (error) {
      return false;
    }
  }

  function stopKitchenToneLoop() {
    if (!alertToneTimer) return;
    window.clearInterval(alertToneTimer);
    alertToneTimer = null;
  }

  function playRepeatingKitchenTone(durationMs = 5000) {
    if (!alertsEnabled) return;
    stopKitchenToneLoop();
    const endAt = Date.now() + durationMs;
    playKitchenTone();
    alertToneTimer = window.setInterval(() => {
      if (Date.now() >= endAt) {
        stopKitchenToneLoop();
        return;
      }
      playKitchenTone();
    }, 850);
    window.setTimeout(stopKitchenToneLoop, durationMs + 250);
  }

  function announceNewOrder(messageText = "New order") {
    if (!alertsEnabled || !("speechSynthesis" in window) || !("SpeechSynthesisUtterance" in window)) return;
    window.speechSynthesis.cancel();
    const message = new SpeechSynthesisUtterance(messageText);
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
      body: `${order.table_label || "Takeaway"} - ${itemCount} item${itemCount === 1 ? "" : "s"} - ${money(order.total_amount)}`,
      icon: "/static/brand/tea_trust_logo.png",
    });
  }

  function alertForNewOrder(order) {
    if (activeStoreId && order.store_id && String(order.store_id) !== String(activeStoreId)) return;
    knownOrderIds.add(Number(order.id));
    playRepeatingKitchenTone(5000);
    announceNewOrder();
    showOrderNotification(order);
  }

  async function enableAlerts() {
    alertsEnabled = true;
    localStorage.setItem("qrCafeAdminAlerts", "on");
    const unlocked = await unlockAlertAudio();
    if ("Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission().catch(() => {});
    }
    renderAlertState();
    if (unlocked) {
      playKitchenTone();
    }
  }

  function armAlertsFromGesture() {
    if (!alertsEnabled || audioUnlocked) return;
    unlockAlertAudio().catch(() => {});
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
    return `
      <select class="status-select status-${order.status}" data-status-for="${order.id}" aria-label="Order status">
        ${statusValues.map((status) => (
          `<option value="${status}" ${status === order.status ? "selected" : ""}>${statusLabel(status)}</option>`
        )).join("")}
      </select>
    `;
  }

  function counterItemTotal() {
    return counterItems.reduce((total, item) => total + Number(item.price || 0) * Number(item.quantity || 0), 0);
  }

  function counterItemNo(item) {
    return String(item?.id || "");
  }

  function counterItemLabel(item) {
    return `No ${counterItemNo(item)} - ${item.name}`;
  }

  function normalizedCounterQuery(value) {
    return String(value || "").trim().toLowerCase();
  }

  function productNumberFromQuery(query) {
    return normalizedCounterQuery(query)
      .replace(/^product\s+/, "")
      .replace(/^item\s+/, "")
      .replace(/^no\.?\s*/, "")
      .replace(/^#/, "")
      .trim();
  }

  function exactCounterItemFromSearch() {
    const query = normalizedCounterQuery(counterItemSearch?.value);
    if (!query) return null;
    const productNo = productNumberFromQuery(query);
    if (/^\d+$/.test(productNo)) {
      const exactNumberMatch = menuItems.find((item) => counterItemNo(item) === productNo);
      if (exactNumberMatch) return exactNumberMatch;
    }
    return menuItems.find((item) => normalizedCounterQuery(item.name) === query) || null;
  }

  function counterSearchMatches(item, query) {
    const normalizedQuery = normalizedCounterQuery(query);
    if (!normalizedQuery) return true;
    const productNo = productNumberFromQuery(normalizedQuery);
    if (/^\d+$/.test(productNo)) {
      return counterItemNo(item).startsWith(productNo);
    }
    const haystack = [
      counterItemNo(item),
      `#${counterItemNo(item)}`,
      `no ${counterItemNo(item)}`,
      item.name,
      item.category_name,
      item.description,
      ...(item.tags || []),
    ].join(" ").toLowerCase();
    return normalizedQuery.split(/\s+/).every((word) => haystack.includes(word));
  }

  function counterSearchRank(item, query) {
    const normalizedQuery = normalizedCounterQuery(query);
    if (!normalizedQuery) return 0;
    const productNo = productNumberFromQuery(normalizedQuery);
    const itemNo = counterItemNo(item);
    const itemName = normalizedCounterQuery(item.name);
    if (/^\d+$/.test(productNo)) {
      if (itemNo === productNo) return 0;
      if (itemNo.startsWith(productNo)) return 1;
    }
    if (itemName === normalizedQuery) return 0;
    if (itemName.startsWith(normalizedQuery)) return 1;
    if (itemName.includes(normalizedQuery)) return 2;
    return 3;
  }

  function filteredCounterMenuItems() {
    const query = counterItemSearch?.value || "";
    return menuItems
      .filter((item) => counterSearchMatches(item, query))
      .sort((first, second) => counterSearchRank(first, query) - counterSearchRank(second, query))
      .slice(0, 60);
  }

  function closeCounterSuggestions() {
    if (!counterItemSuggestions) return;
    counterItemSuggestions.hidden = true;
    counterItemSearch?.setAttribute("aria-expanded", "false");
    counterItemSearch?.removeAttribute("aria-activedescendant");
  }

  function renderCounterSuggestions(matchingItems) {
    if (!counterItemSuggestions || !counterItemSearch) return;
    const isSearchActive = document.activeElement === counterItemSearch;
    if (!isSearchActive) {
      closeCounterSuggestions();
      return;
    }
    const visibleItems = matchingItems.slice(0, 8);
    counterSuggestionIndex = Math.max(0, Math.min(counterSuggestionIndex, Math.max(visibleItems.length - 1, 0)));
    if (!visibleItems.length) {
      counterItemSuggestions.innerHTML = `<p class="counter-suggestion-empty">No matching product</p>`;
      counterItemSuggestions.hidden = false;
      counterItemSearch.setAttribute("aria-expanded", "true");
      counterItemSearch.removeAttribute("aria-activedescendant");
      return;
    }
    counterItemSuggestions.innerHTML = visibleItems.map((item, index) => {
      const suggestionId = `counterSuggestion${item.id}`;
      return `
        <button
          id="${suggestionId}"
          class="counter-suggestion ${index === counterSuggestionIndex ? "is-active" : ""}"
          data-counter-suggestion="${item.id}"
          type="button"
          role="option"
          aria-selected="${index === counterSuggestionIndex ? "true" : "false"}"
        >
          <span class="counter-suggestion-no">No ${escapeHtml(counterItemNo(item))}</span>
          <span class="counter-suggestion-name">${escapeHtml(item.name)}</span>
          <span class="counter-suggestion-price">${money(item.price)}</span>
        </button>
      `;
    }).join("");
    counterItemSuggestions.hidden = false;
    counterItemSearch.setAttribute("aria-expanded", "true");
    counterItemSearch.setAttribute("aria-activedescendant", `counterSuggestion${visibleItems[counterSuggestionIndex]?.id || ""}`);
  }

  function renderCounterOrder() {
    if (!counterOrderForm) return;
    const selectedTable = counterTableSelect?.value || "";
    const selectedItem = counterItemSelect?.value || "";
    const matchingItems = filteredCounterMenuItems();
    const exactSearchItem = exactCounterItemFromSearch();
    if (counterTableSelect) {
      counterTableSelect.innerHTML = `
        <option value="">Select table</option>
        ${tables.map((table) => `<option value="${table.id}">${escapeHtml(table.label)}</option>`).join("")}
      `;
      counterTableSelect.value = selectedTable;
    }
    if (counterItemSelect) {
      counterItemSelect.innerHTML = `
        <option value="">${matchingItems.length ? "Select menu item" : "No matching product"}</option>
        ${matchingItems.map((item) => `<option value="${item.id}">${escapeHtml(counterItemLabel(item))} - ${money(item.price)}</option>`).join("")}
      `;
      counterItemSelect.value = matchingItems.some((item) => String(item.id) === String(selectedItem))
        ? selectedItem
        : (exactSearchItem?.id || matchingItems[0]?.id || "");
    }
    if (counterOrderItems) {
      counterOrderItems.innerHTML = counterItems.map((item) => `
        <div class="counter-order-line">
          <span>${escapeHtml(item.name)} x ${item.quantity}</span>
          <strong>${money(Number(item.price) * Number(item.quantity))}</strong>
          <button class="icon-button" data-remove-counter-item="${item.id}" type="button" aria-label="Remove ${escapeHtml(item.name)}">Remove</button>
        </div>
      `).join("") || `<p class="helper-text">No items added yet.</p>`;
    }
    if (counterOrderTotal) {
      counterOrderTotal.textContent = money(counterItemTotal());
    }
    renderCounterSuggestions(matchingItems);
  }

  function selectedCounterItem() {
    const exactItem = exactCounterItemFromSearch();
    if (exactItem) return exactItem;
    return menuItems.find((candidate) => String(candidate.id) === String(counterItemSelect?.value))
      || filteredCounterMenuItems()[0]
      || null;
  }

  function addCounterItem(itemToAdd = null) {
    const item = itemToAdd || selectedCounterItem();
    const quantity = Math.max(1, Number(counterItemQty?.value || 1));
    if (!item) {
      if (counterOrderMessage) counterOrderMessage.textContent = "Select a menu item first.";
      return;
    }
    const existing = counterItems.find((candidate) => String(candidate.id) === String(item.id));
    if (existing) {
      existing.quantity += quantity;
    } else {
      counterItems.push({ id: item.id, name: item.name, price: item.price, quantity });
    }
    if (counterItemQty) counterItemQty.value = "1";
    if (counterItemSearch) {
      counterItemSearch.value = "";
      counterItemSearch.focus();
    }
    if (counterOrderMessage) counterOrderMessage.textContent = "";
    renderCounterOrder();
  }

  async function submitCounterOrder(event) {
    event.preventDefault();
    if (!counterTableSelect?.value) {
      counterOrderMessage.textContent = "Select the customer table.";
      return;
    }
    if (!counterItems.length) {
      counterOrderMessage.textContent = "Add at least one item.";
      return;
    }
    counterOrderMessage.textContent = "Creating counter order...";
    const submitButton = counterOrderForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    try {
      const order = await apiFetch("/api/v1/orders", {
        method: "POST",
        body: {
          table_id: counterTableSelect.value,
          store_id: activeStoreId,
          customer_name: counterCustomerName?.value || "Counter Guest",
          customer_phone: counterCustomerPhone?.value || "",
          notes: counterOrderNotes?.value || "Counter order",
          payment_method: "cash",
          items: counterItems.map((item) => ({
            menu_item_id: Number(item.id),
            quantity: Number(item.quantity),
          })),
        },
      });
      counterItems = [];
      counterOrderForm.reset();
      counterOrderMessage.textContent = `Created ${order.order_number}`;
      dashboardDataSignature = "";
      renderCounterOrder();
      await load();
    } catch (error) {
      counterOrderMessage.textContent = error.message;
    } finally {
      submitButton.disabled = false;
    }
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
    }
    return actions.map(([status, label]) => (
      `<button class="button mini-button ${status === "cancelled" ? "danger" : ""}" data-quick-status="${status}" data-order-id="${order.id}" type="button">${label}</button>`
    )).join("");
  }

  async function updateOrderStatus(orderId, status, cancellationReason = "") {
    await apiFetch(urlWithStore(`/api/v1/admin/orders/${orderId}/status`), {
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
    const statusActions = quickStatusButtons(order);
    orderDetailTitle.textContent = `${order.order_number} - ${order.table_label || "Takeaway"}`;
    orderDetailBody.innerHTML = `
      ${receiptHtml(order, { showCustomer: true })}
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
    selectedOrder = order;
    seenOrderIds.add(Number(order.id));
    saveSeenOrders();
    render();
    renderOrderDetail(order);
    orderDialog.showModal();
  }

  printOrderBillButton?.addEventListener("click", () => {
    if (selectedOrder) printBill(selectedOrder);
  });

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
      ["cash_pending", "paid"].includes(order.payment_status)
    ));
  }

  function renderMetrics() {
    const revenue = activeRevenueOrders().reduce((sum, order) => sum + Number(order.total_amount || 0), 0);
    const pending = orders.filter((order) => order.status === "pending").length;
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
    document.getElementById("activeTablesMetric").textContent = `${tables.length} active`;
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
      recentBody.innerHTML = visibleOrders.slice(0, recentOrderLimit).map((order) => {
        const itemsCount = (order.items || []).reduce((sum, item) => sum + Number(item.quantity || 0), 0);
        return `
          <tr class="${isUnseen(order) ? "is-unseen" : ""}">
            <td><strong>${escapeHtml(order.order_number)}</strong></td>
            <td>${escapeHtml(order.table_label || "Takeaway")}</td>
            <td>${itemsCount} item${itemsCount === 1 ? "" : "s"}</td>
            <td>${dashboardMoney(order.total_amount)}</td>
            <td>${statusSelectHtml(order)}</td>
            <td>${timeAgo(order.created_at)}</td>
            <td>
              <div class="order-inline-actions">
                <button class="button mini-button" data-view-order="${order.id}" type="button">View</button>
                <button class="button mini-button" data-save-status="${order.id}" type="button">Save</button>
                ${quickStatusButtons(order)}
              </div>
            </td>
          </tr>
        `;
      }).join("") || `<tr><td colspan="7" class="empty-cell">No orders found.</td></tr>`;
    }

    board.innerHTML = visibleOrders.slice(0, recentOrderLimit).map((order) => {
      const items = order.items.map((item) => `<li>${escapeHtml(item.item_name)} x ${item.quantity}</li>`).join("");
      return `
        <article class="order-card ${isUnseen(order) ? "is-unseen" : ""}" data-order-id="${order.id}">
          <header>
            <div>
              <strong>${escapeHtml(order.order_number)}</strong>
              <p class="helper-text">${escapeHtml(order.table_label || "Takeaway")} - ${money(order.total_amount)}</p>
            </div>
            <span class="status-pill status-${order.status}">${escapeHtml(order.status.replaceAll("_", " "))}</span>
          </header>
          <p><strong>Token:</strong> ${order.token_number || "Pending"}</p>
          <ul>${items}</ul>
          <div class="order-actions">
            ${statusSelectHtml(order)}
            <button class="button" data-save-status="${order.id}" type="button">Update</button>
            <button class="button" data-view-order="${order.id}" type="button">View</button>
            ${quickStatusButtons(order)}
          </div>
        </article>
      `;
    }).join("") || `<p class="helper-text">No orders found.</p>`;

    renderMetrics();
    renderTopItems();
    renderSalesChart();
    renderCounterOrder();
  }

  function trackNewOrderAlerts(orderPayload) {
    const activeStatuses = new Set(["pending", "preparing", "ready"]);
    const newOrders = orderPayload.filter((order) => (
      activeStatuses.has(order.status) && !knownOrderIds.has(Number(order.id))
    ));

    if (hasLoadedDashboard) {
      newOrders.forEach(alertForNewOrder);
    }

    knownOrderIds = new Set(orderPayload.map((order) => Number(order.id)));
    hasLoadedDashboard = true;
  }

  async function load() {
    if (isLoading) return;
    isLoading = true;
    try {
      const [orderPayload, tablePayload, menuPayload] = await Promise.all([
        apiFetch(urlWithStore("/api/v1/admin/orders")),
        apiFetch(urlWithStore("/api/v1/admin/tables")),
        menuItems.length ? Promise.resolve({ items: menuItems }) : apiFetch(urlWithStore("/api/v1/menu")),
      ]);
      const nextSignature = JSON.stringify({ orders: orderPayload, tables: tablePayload });
      if (nextSignature === dashboardDataSignature) {
        return;
      }
      dashboardDataSignature = nextSignature;
      trackNewOrderAlerts(orderPayload);
      orders = orderPayload;
      tables = tablePayload;
      menuItems = (menuPayload.items || []).filter((item) => item.is_available);
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

  counterAddItem?.addEventListener("click", () => addCounterItem());
  counterItemSearch?.addEventListener("focus", () => {
    counterSuggestionIndex = 0;
    renderCounterOrder();
  });
  counterItemSearch?.addEventListener("blur", () => {
    window.setTimeout(closeCounterSuggestions, 120);
  });
  counterItemSearch?.addEventListener("input", () => {
    counterSuggestionIndex = 0;
    renderCounterOrder();
  });
  counterItemSearch?.addEventListener("keydown", (event) => {
    const suggestionItems = filteredCounterMenuItems().slice(0, 8);
    if ((event.key === "ArrowDown" || event.key === "ArrowUp") && suggestionItems.length) {
      event.preventDefault();
      const direction = event.key === "ArrowDown" ? 1 : -1;
      counterSuggestionIndex = (counterSuggestionIndex + direction + suggestionItems.length) % suggestionItems.length;
      if (counterItemSelect) counterItemSelect.value = suggestionItems[counterSuggestionIndex].id;
      renderCounterSuggestions(suggestionItems);
      return;
    }
    if (event.key === "Escape") {
      closeCounterSuggestions();
      return;
    }
    if (event.key !== "Enter") return;
    event.preventDefault();
    addCounterItem();
  });
  counterItemSuggestions?.addEventListener("mousedown", (event) => {
    const button = event.target.closest("[data-counter-suggestion]");
    if (!button) return;
    event.preventDefault();
    const item = menuItems.find((candidate) => String(candidate.id) === String(button.dataset.counterSuggestion));
    if (!item) return;
    if (counterItemSelect) counterItemSelect.value = item.id;
    addCounterItem(item);
    closeCounterSuggestions();
  });
  counterItemQty?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    addCounterItem();
  });
  counterOrderItems?.addEventListener("click", (event) => {
    const removeButton = event.target.closest("[data-remove-counter-item]");
    if (!removeButton) return;
    counterItems = counterItems.filter((item) => String(item.id) !== String(removeButton.dataset.removeCounterItem));
    renderCounterOrder();
  });
  counterOrderForm?.addEventListener("submit", submitCounterOrder);

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
  document.addEventListener("pointerdown", armAlertsFromGesture, { capture: true });
  document.addEventListener("keydown", armAlertsFromGesture, { capture: true });
  renderAlertState();
  const socket = connectSocket();
  if (socket) {
    socket.on("connect", () => {
      socket.emit("admin_join", { store_id: activeStoreId });
    });
    if (socket.connected) {
      socket.emit("admin_join", { store_id: activeStoreId });
    }
    socket.on("order_created", (order) => {
      if (activeStoreId && order.store_id && String(order.store_id) !== String(activeStoreId)) return;
      alertForNewOrder(order);
      dashboardDataSignature = "";
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
        <strong>${escapeHtml(order.table_label || "Takeaway")}</strong>
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
    const orders = await apiFetch(urlWithStore("/api/v1/admin/orders"));
    const active = orders.filter((order) => ["pending", "preparing", "ready"].includes(order.status));
    const nextSignature = JSON.stringify({ active });
    if (nextSignature === signature) return;
    signature = nextSignature;
    render(active);
  }

  board.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-kitchen-status]");
    if (!button) return;
    await apiFetch(urlWithStore(`/api/v1/admin/orders/${button.dataset.orderId}/status`), {
      method: "PATCH",
      body: { status: button.dataset.kitchenStatus },
    });
    signature = "";
    await load();
  });

  const socket = connectSocket();
  if (socket) {
    socket.emit("admin_join", { store_id: selectedStoreId() });
    socket.on("order_created", (order) => {
      const storeId = selectedStoreId();
      if (storeId && order.store_id && String(order.store_id) !== String(storeId)) return;
      load();
    });
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
  const ordersExportLink = document.getElementById("ordersExportLink");

  if (ordersExportLink) {
    ordersExportLink.href = urlWithStore(ordersExportLink.getAttribute("href") || "/api/v1/admin/export/orders.csv");
  }

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
        <strong data-hour-height="${Math.max(4, (bucket.orders / maxOrders) * 100)}"></strong>
        <small>${bucket.orders}</small>
      </div>
    `).join("");
    hourly.querySelectorAll("[data-hour-height]").forEach((bar) => {
      bar.style.height = `${bar.dataset.hourHeight}%`;
    });
  }

  async function load() {
    const payload = await apiFetch(urlWithStore(`/api/v1/admin/analytics?days=${range.value}`));
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
    const payload = await apiFetch(urlWithStore("/api/v1/menu?include_unavailable=1"));
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
    await apiFetch(urlWithStore("/api/v1/admin/menu-items"), {
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
    await apiFetch(urlWithStore("/api/v1/admin/categories"), {
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
      await apiFetch(urlWithStore(`/api/v1/admin/menu-items/${itemId}`), {
        method: "PATCH",
        body: collectRow(row),
      });
      const image = row.querySelector('[name="image"]').files[0];
      if (image) {
        const form = new FormData();
        form.append("image", image);
        await apiFetch(urlWithStore(`/api/v1/admin/menu-items/${itemId}/image`), {
          method: "POST",
          body: form,
        });
      }
      await load();
    }
    if (del && window.confirm("Delete this menu item?")) {
      await apiFetch(urlWithStore(`/api/v1/admin/menu-items/${del.dataset.deleteItem}`), { method: "DELETE" });
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

  function qrImageUrl(table, size = 260) {
    const url = new URL(table.qr_image_url || `/qr/table/${table.id}.png`, window.location.origin);
    url.searchParams.set("size", size);
    return url.toString();
  }

  function posterSvg(table) {
    const menuUrl = `${window.location.origin}${table.menu_url}`;
    const logoUrl = `${window.location.origin}/static/brand/tea_trust_logo.png`;
    const qrUrl = qrImageUrl(table, 520);
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
    link.download = `${filenamePart(cafeName)}-${table.qr_slug}-poster.svg`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  function tableCardHtml(table) {
    const menuUrl = `${window.location.origin}${table.menu_url}`;
    const qrUrl = qrImageUrl(table);
    return `
      <article class="admin-row table-qr-row" data-table-row="${table.id}">
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
          <div class="table-edit-grid">
            <input name="table_number" type="number" min="1" value="${table.table_number}" aria-label="Table number">
            <input name="label" value="${escapeHtml(table.label)}" aria-label="Table label">
            <label class="check-row"><input type="checkbox" name="is_active" ${table.is_active ? "checked" : ""}> Active</label>
          </div>
          <div class="row-actions">
            <a class="button mini-button" href="${escapeHtml(qrUrl)}" download="${filenamePart(cafeName)}-${escapeHtml(table.qr_slug)}.png">Download QR</a>
            <button class="button mini-button" data-download-poster="${table.id}" type="button">Download poster</button>
            <button class="button mini-button" data-print-qr="${table.id}" type="button">Print poster</button>
            <button class="button mini-button" data-copy-table-url="${table.id}" type="button">Copy link</button>
            <button class="button mini-button" data-save-table="${table.id}" type="button">Save table</button>
          </div>
        </div>
      </article>
    `;
  }

  function printTables(tables) {
    const stylesheetUrl = document.querySelector('link[rel="stylesheet"][href*="main.css"]')?.href
      || `${window.location.origin}/static/css/main.css`;
    const content = tables.map((table) => {
      const menuUrl = `${window.location.origin}${table.menu_url}`;
      return `
        <section class="print-qr-card">
          <header class="print-head">
            <img class="print-logo" src="/static/brand/tea_trust_logo.png" alt="">
            <strong>${escapeHtml(cafeName)}</strong>
          </header>
          <div class="print-body">
            <p class="print-kicker">Scan to order</p>
            <h1>${escapeHtml(table.label)}</h1>
            <div class="print-qr-frame">
              <img class="print-qr" src="${escapeHtml(qrImageUrl(table, 520))}" alt="QR code for ${escapeHtml(table.label)}">
            </div>
            <p class="print-help">Open camera, scan, and place your order</p>
            <small>${escapeHtml(menuUrl)}</small>
          </div>
        </section>
      `;
    }).join("");
    const printWindow = window.open("", `qr-print-${Date.now()}`);
    if (!printWindow) return;
    printWindow.document.open();
    printWindow.document.write(`
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Table QR Codes</title>
          <link rel="stylesheet" href="${escapeHtml(stylesheetUrl)}">
        </head>
        <body class="qr-print-page"><main class="print-grid">${content}</main></body>
      </html>
    `);
    printWindow.document.close();
    const stylesheet = printWindow.document.querySelector('link[rel="stylesheet"]');
    const images = [...printWindow.document.images];
    let printed = false;
    const printReady = () => {
      if (printed) return;
      printed = true;
      printWindow.focus();
      printWindow.print();
    };
    const stylesheetLoad = stylesheet
      ? new Promise((resolve) => {
        stylesheet.addEventListener("load", resolve, { once: true });
        stylesheet.addEventListener("error", resolve, { once: true });
      })
      : Promise.resolve();
    const imageLoads = images.map((image) => {
      if (image.complete) return Promise.resolve();
      return new Promise((resolve) => {
        image.addEventListener("load", resolve, { once: true });
        image.addEventListener("error", resolve, { once: true });
      });
    });
    Promise.all([stylesheetLoad, ...imageLoads]).then(printReady);
    window.setTimeout(printReady, 2400);
  }

  async function load() {
    tableRows = await apiFetch(urlWithStore("/api/v1/admin/tables?include_inactive=1"));
    list.innerHTML = tableRows.map(tableCardHtml).join("") || `<p class="helper-text">No tables found.</p>`;
  }

  list.addEventListener("click", async (event) => {
    const printButton = event.target.closest("[data-print-qr]");
    const downloadButton = event.target.closest("[data-download-poster]");
    const copyButton = event.target.closest("[data-copy-table-url]");
    const saveButton = event.target.closest("[data-save-table]");
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
    if (saveButton) {
      const row = saveButton.closest("[data-table-row]");
      await apiFetch(urlWithStore(`/api/v1/admin/tables/${saveButton.dataset.saveTable}`), {
        method: "PATCH",
        body: {
          table_number: row.querySelector('[name="table_number"]').value,
          label: row.querySelector('[name="label"]').value,
          is_active: row.querySelector('[name="is_active"]').checked,
        },
      });
      saveButton.textContent = "Saved";
      window.setTimeout(() => { saveButton.textContent = "Save table"; }, 1200);
      await load();
    }
  });

  printAllButton?.addEventListener("click", () => printTables(tableRows.filter((table) => table.is_active)));

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    await apiFetch(urlWithStore("/api/v1/admin/tables"), {
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

function initAdminSettings() {
  const list = document.getElementById("staffProfilesList");
  if (!list) return;
  const form = document.getElementById("staffProfileForm");
  const roleSelect = document.getElementById("staffRoleSelect");
  const storeSelect = document.getElementById("staffStoreSelect");
  const summary = document.getElementById("staffProfileSummary");
  const broadcastForm = document.getElementById("broadcastForm");
  const broadcastSummary = document.getElementById("broadcastContactSummary");
  const broadcastStatus = document.getElementById("broadcastStatus");
  const broadcastSendButton = document.getElementById("broadcastSendButton");
  let roles = [];
  let stores = [];
  let staff = [];
  let broadcastContacts = [];

  function roleOptionsHtml(selectedRole = "counter") {
    return roles.map((role) => (
      `<option value="${escapeHtml(role.value)}" ${role.value === selectedRole ? "selected" : ""}>${escapeHtml(role.label)}</option>`
    )).join("");
  }

  function storeOptionsHtml(selectedStoreId = "", includeAll = true) {
    return [
      includeAll ? `<option value="">All stores</option>` : "",
      ...stores.map((store) => (
        `<option value="${store.id}" ${String(store.id) === String(selectedStoreId || "") ? "selected" : ""}>${escapeHtml(store.name)}</option>`
      )),
    ].join("");
  }

  function render() {
    if (roleSelect) {
      roleSelect.innerHTML = roleOptionsHtml("counter");
    }
    if (storeSelect) {
      storeSelect.innerHTML = storeOptionsHtml(selectedStoreId(), false);
      storeSelect.value = stores.some((store) => String(store.id) === String(selectedStoreId()))
        ? String(selectedStoreId())
        : String(stores[0]?.id || "");
    }
    if (summary) {
      const activeCount = staff.filter((user) => user.active).length;
      summary.textContent = `${activeCount} active`;
    }
    if (broadcastSummary) {
      broadcastSummary.textContent = `${broadcastContacts.length} opted in`;
    }
    if (broadcastSendButton) {
      broadcastSendButton.disabled = broadcastContacts.length === 0;
    }
    list.innerHTML = staff.map((user) => `
      <article class="admin-row staff-profile-row" data-staff-row="${user.id}">
        <div>
          <strong>${escapeHtml(user.username)}</strong>
          <p class="helper-text">${escapeHtml(user.role_label)} - ${escapeHtml(user.store_name || "All stores")}${user.email ? ` - ${escapeHtml(user.email)}` : ""}</p>
        </div>
        <div class="staff-profile-edit-grid">
          <input name="username" value="${escapeHtml(user.username)}" aria-label="Username">
          <input name="email" type="email" value="${escapeHtml(user.email)}" aria-label="Email">
          <select name="role" aria-label="Profile role">${roleOptionsHtml(user.role)}</select>
          <select name="store_id" aria-label="Assigned store">${storeOptionsHtml(user.store_id)}</select>
          <input name="password" type="password" placeholder="New password" autocomplete="new-password" minlength="12" aria-label="New password">
          <label class="check-row"><input type="checkbox" name="active" ${user.active ? "checked" : ""}> Active</label>
          <div class="staff-profile-actions">
            <button class="button mini-button" data-save-staff="${user.id}" type="button">Save</button>
            <button class="button danger mini-button" data-delete-staff="${user.id}" data-staff-name="${escapeHtml(user.username)}" type="button">Delete</button>
          </div>
        </div>
      </article>
    `).join("") || `<p class="helper-text">No staff profiles found.</p>`;
  }

  async function load() {
    const [staffPayload, contactPayload] = await Promise.all([
      apiFetch("/api/v1/admin/staff"),
      apiFetch(urlWithStore("/api/v1/admin/customers?marketing_only=1")),
    ]);
    roles = staffPayload.roles || [];
    stores = staffPayload.stores || storeOptions;
    staff = staffPayload.staff || [];
    broadcastContacts = contactPayload || [];
    render();
  }

  broadcastForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(broadcastForm);
    broadcastSendButton.disabled = true;
    broadcastStatus.textContent = "Sending...";
    try {
      const result = await apiFetch(urlWithStore("/api/v1/admin/broadcasts"), {
        method: "POST",
        body: {
          message: data.get("message"),
        },
      });
      broadcastStatus.textContent = `Sent ${result.sent} of ${result.recipient_count}`;
      if (result.mode && result.mode !== "none") {
        broadcastStatus.textContent += ` via ${result.mode.replaceAll("_", " ")}`;
      }
      if (result.failed) {
        broadcastStatus.textContent += `, ${result.failed} failed`;
        const firstFailure = result.failures?.[0]?.error;
        if (firstFailure) {
          broadcastStatus.textContent += `: ${firstFailure}`;
        }
      }
      broadcastForm.reset();
      await load();
    } catch (error) {
      broadcastStatus.textContent = error.message;
    } finally {
      broadcastSendButton.disabled = broadcastContacts.length === 0;
    }
  });

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    await apiFetch("/api/v1/admin/staff", {
      method: "POST",
      body: {
        username: data.get("username"),
        email: data.get("email"),
        role: data.get("role"),
        store_id: data.get("store_id"),
        password: data.get("password"),
      },
    });
    form.reset();
    await load();
  });

  list.addEventListener("click", async (event) => {
    const deleteButton = event.target.closest("[data-delete-staff]");
    if (deleteButton) {
      const staffName = deleteButton.dataset.staffName || "this profile";
      if (!window.confirm(`Delete ${staffName}?`)) return;
      await apiFetch(`/api/v1/admin/staff/${deleteButton.dataset.deleteStaff}`, {
        method: "DELETE",
      });
      await load();
      return;
    }

    const saveButton = event.target.closest("[data-save-staff]");
    if (!saveButton) return;
    const row = saveButton.closest("[data-staff-row]");
    await apiFetch(`/api/v1/admin/staff/${saveButton.dataset.saveStaff}`, {
      method: "PATCH",
      body: {
        username: row.querySelector('[name="username"]').value,
        email: row.querySelector('[name="email"]').value,
        role: row.querySelector('[name="role"]').value,
        store_id: row.querySelector('[name="store_id"]').value,
        active: row.querySelector('[name="active"]').checked,
        password: row.querySelector('[name="password"]').value,
      },
    });
    saveButton.textContent = "Saved";
    window.setTimeout(() => { saveButton.textContent = "Save"; }, 1200);
    await load();
  });

  load().catch((error) => {
    list.innerHTML = `<p class="helper-text">${escapeHtml(error.message)}</p>`;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupStoreSelector();
  if (pageId === "customer-menu") initCustomerMenu();
  if (pageId === "customer-cart" || pageId === "customer-checkout") initCustomerCartPage();
  if (pageId === "order-status") initOrderStatus();
  if (pageId === "admin-dashboard") initAdminDashboard();
  if (pageId === "admin-kitchen") initKitchenDisplay();
  if (pageId === "admin-analytics") initAdminAnalytics();
  if (pageId === "admin-menu") initAdminMenu();
  if (pageId === "admin-tables") initAdminTables();
  if (pageId === "admin-settings") initAdminSettings();
});
