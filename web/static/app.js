const tg = window.Telegram?.WebApp;
const initData = tg ? tg.initData : "";

const state = {
  me: { user_id: 0, is_admin: false, first_name: "" },
  catalog: [],
  cart: { items: [], total: 0, count: 0 },
  view: "catalog",
  categoryId: null,
  productId: null,
  orders: [],
  adminOrders: [],
  adminFilter: "",
  adminOrderId: null,
};

const STATUS = {
  new: { label: "Новый", cls: "new" },
  processing: { label: "В работе", cls: "processing" },
  done: { label: "Выполнен", cls: "done" },
  cancelled: { label: "Отменён", cls: "cancelled" },
};
const ADMIN_TABS = [
  ["", "Все"],
  ["new", "Новые"],
  ["processing", "В работе"],
  ["done", "Выполнен"],
  ["cancelled", "Отменён"],
];

const $ = (sel) => document.querySelector(sel);
const view = $("#view");
const fmt = (n) => new Intl.NumberFormat("ru-RU").format(n);
const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function buzz(type = "light") {
  try { tg?.HapticFeedback?.impactOccurred(type); } catch (e) {}
}

let toastTimer;
function toast(msg, type = "ok") {
  const el = $("#toast");
  el.textContent = msg;
  el.className = "toast show " + type;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.className = "toast"), 2300);
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    method: opts.method || "GET",
    headers: { "Content-Type": "application/json", "X-Init-Data": initData },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  let data;
  try { data = await res.json(); } catch (e) { data = { ok: false, error: "Ошибка соединения" }; }
  if (!res.ok || !data.ok) throw new Error(data.error || "Ошибка запроса");
  return data;
}

/* ---------- init ---------- */
async function init() {
  if (!tg || !tg.initData) {
    view.innerHTML =
      '<div class="empty"><div class="e-ico">📱</div><div class="e-title">Откройте в Telegram</div>' +
      '<p>Это мини-приложение Telegram. Откройте его через бота DevShop.</p></div>';
    return;
  }
  tg.ready();
  tg.expand();
  try { tg.setHeaderColor("#0f1117"); tg.setBackgroundColor("#0f1117"); } catch (e) {}

  view.innerHTML = renderSkeleton();

  try {
    state.me = await api("/api/me");
    state.catalog = (await api("/api/catalog")).categories;
    state.cart = await api("/api/cart");
  } catch (e) {
    view.innerHTML = `<div class="empty"><div class="e-ico">⚠️</div><div class="e-title">Не удалось загрузить магазин</div><p>${esc(e.message)}</p></div>`;
    return;
  }

  $("#adminNav").classList.toggle("hidden", !state.me.is_admin);
  if (state.catalog.length) state.categoryId = state.catalog[0].id;
  updateCartBadge();
  show("catalog");
}

/* ---------- navigation ---------- */
function show(name) {
  state.view = name;
  $("#view").classList.remove("hidden");
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.nav === name));
  $("#backBtn").classList.toggle("hidden", !["product", "checkout", "admin-order"].includes(name));
  $("#cartBadge").classList.toggle("hidden", state.cart.count === 0 && name !== "cart");
  $("#title").textContent = {
    catalog: "DevShop", product: "Товар", cart: "Корзина", checkout: "Оформление",
    orders: "Мои заказы", admin: "Админ-панель", "admin-order": "Заказ",
    success: "Заказ",
  }[name] || "DevShop";

  if (name === "catalog") renderCatalog();
  else if (name === "product") renderProduct();
  else if (name === "cart") renderCart();
  else if (name === "checkout") renderCheckout();
  else if (name === "orders") renderOrders();
  else if (name === "admin") renderAdmin();
  else if (name === "admin-order") renderAdminOrder();
  else if (name === "success") renderSuccess();
}

const showCart = () => show("cart");

function goBack() {
  buzz();
  if (state.view === "product") show("catalog");
  else if (state.view === "checkout") show("cart");
  else if (state.view === "admin-order") show("admin");
}

function updateCartBadge() {
  $("#cartCount").textContent = state.cart.count;
  $("#navCartCount").textContent = state.cart.count;
  $("#navCartCount").classList.toggle("hidden", state.cart.count === 0);
  $("#cartBadge").classList.toggle("hidden", state.cart.count === 0 && state.view !== "cart");
}

/* ---------- loaders & effects ---------- */
function renderSkeleton() {
  return `
    <div class="skel-row">
      ${Array.from({ length: 4 }, () => '<div class="skel skel-chip"></div>').join("")}
    </div>
    <div class="grid">
      ${Array.from({ length: 6 }, () => '<div class="skel skel-card"></div>').join("")}
    </div>`;
}

function orderSkeleton() {
  return Array.from(
    { length: 4 },
    () => '<div class="detail-block"><div class="skel skel-line w60"></div><div class="skel skel-line"></div></div>'
  ).join("");
}

function flyToCart(fromEl) {
  const cartEl = $("#cartBadge");
  if (!cartEl || cartEl.classList.contains("hidden")) return;
  const a = fromEl.getBoundingClientRect();
  const b = cartEl.getBoundingClientRect();
  const dot = document.createElement("span");
  dot.className = "fly-dot";
  dot.style.left = a.left + a.width / 2 - 6 + "px";
  dot.style.top = a.top + a.height / 2 - 6 + "px";
  document.body.appendChild(dot);
  requestAnimationFrame(() =>
    requestAnimationFrame(() => {
      dot.style.transform =
        `translate(${b.left + b.width / 2 - (a.left + a.width / 2)}px, ` +
        `${b.top + b.height / 2 - (a.top + a.height / 2)}px) scale(0.3)`;
      dot.style.opacity = "0.2";
    })
  );
  setTimeout(() => dot.remove(), 650);
}

function confetti() {
  const colors = ["#4f7cff", "#8faaff", "#3d66e0", "#eceef2"];
  const wrap = document.createElement("div");
  wrap.className = "confetti-wrap";
  document.body.appendChild(wrap);
  for (let i = 0; i < 48; i++) {
    const p = document.createElement("span");
    p.className = "confetti-p";
    p.style.left = 28 + Math.random() * 44 + "%";
    p.style.background = colors[i % colors.length];
    p.style.setProperty("--dx", Math.round(Math.random() * 160 - 80) + "px");
    p.style.setProperty("--r", Math.round(Math.random() * 720 - 360) + "deg");
    p.style.setProperty("--d", Math.round(Math.random() * 300) + "ms");
    p.style.setProperty("--w", Math.round(Math.random() * 6 + 5) + "px");
    p.style.setProperty("--h", Math.round(Math.random() * 8 + 6) + "px");
    wrap.appendChild(p);
  }
  setTimeout(() => wrap.remove(), 2000);
}

/* ---------- catalog ---------- */
function renderCatalog() {
  view.innerHTML = `
    <div class="section-title">Каталог</div>
    <div class="chips">${state.catalog.map((c) =>
      `<button class="chip ${c.id === state.categoryId ? "active" : ""}" data-action="cat" data-id="${c.id}">${c.emoji} ${esc(c.name)}</button>`).join("")}</div>
    ${renderProducts()}`;
}

function renderProducts() {
  const cat = state.catalog.find((c) => c.id === state.categoryId);
  if (!cat) return "";
  return `<div class="grid">${cat.products.map(productCard).join("")}</div>`;
}

function productCard(p) {
  const inCart = state.cart.items.find((i) => i.product_id === p.id);
  return `
    <article class="card" data-action="product" data-id="${p.id}">
      <div class="card-img" style="--emoji:'${p.emoji || "🛍"}'"><img src="${esc(p.photo_url)}" alt="${esc(p.name)}" loading="lazy" onerror="this.remove()"></div>
      <div class="card-body">
        <h3>${esc(p.name)}</h3>
        <p class="card-desc">${esc(p.description)}</p>
        <div class="card-foot">
          <span class="price">${fmt(p.price)} ₽</span>
          <button class="btn-add" data-action="cart-add" data-id="${p.id}" aria-label="В корзину">${inCart ? "✓" : "+"}</button>
        </div>
      </div>
    </article>`;
}

/* ---------- product detail ---------- */
function renderProduct() {
  const cat = state.catalog.find((c) => c.products.some((p) => p.id === state.productId));
  const p = cat?.products.find((x) => x.id === state.productId);
  if (!p) return show("catalog");
  const item = state.cart.items.find((i) => i.product_id === p.id);
  const q = item ? item.quantity : 1;
  view.innerHTML = `
    <div class="detail">
      <div class="detail-img" style="--emoji:'${p.emoji || "🛍"}'"><img src="${esc(p.photo_url)}" alt="${esc(p.name)}" onerror="this.remove()"></div>
      <h1>${esc(p.name)}</h1>
      <p class="desc">${esc(p.description)}</p>
      <div class="stock">✔ В наличии: ${p.stock} шт.</div>
      <div class="detail-foot">
        <span class="detail-price">${fmt(p.price)} ₽</span>
        <div class="qty">
          <button data-action="qty" data-id="${p.id}" data-qty="${q - 1}" aria-label="Меньше">−</button>
          <span>${q}</span>
          <button data-action="qty" data-id="${p.id}" data-qty="${q + 1}" aria-label="Больше">+</button>
        </div>
      </div>
      <button class="btn btn-primary btn-block" style="margin-top:12px" data-action="cart-add" data-id="${p.id}">Добавить в корзину</button>
    </div>`;
}

/* ---------- cart ---------- */
function renderCart() {
  if (!state.cart.items.length) {
    view.innerHTML = `
      <div class="empty">
        <div class="e-ico">🛒</div>
        <div class="e-title">Корзина пуста</div>
        <p>Загляните в каталог и добавьте что-нибудь крутое.</p>
        <button class="btn btn-primary" data-action="nav-catalog">В каталог</button>
      </div>`;
    return;
  }
  view.innerHTML = `
    <div class="section-title">Корзина</div>
    ${state.cart.items.map(cartItemRow).join("")}
    <div class="cart-total"><span class="lbl">Итого</span><span class="val">${fmt(state.cart.total)} ₽</span></div>
    <button class="btn btn-primary btn-block" data-action="checkout">Оформить заказ</button>
    <button class="btn btn-ghost btn-block" style="margin-top:10px" data-action="cart-clear">Очистить корзину</button>`;
}

function cartItemRow(it) {
  return `
    <div class="cart-item">
      <div class="ci-info">
        <div class="ci-name">${esc(it.name)}</div>
        <div class="ci-sub">${fmt(it.price)} ₽ / шт</div>
      </div>
      <div class="qty">
        <button data-action="qty" data-id="${it.product_id}" data-qty="${it.quantity - 1}" aria-label="Меньше">−</button>
        <span>${it.quantity}</span>
        <button data-action="qty" data-id="${it.product_id}" data-qty="${it.quantity + 1}" aria-label="Больше">+</button>
      </div>
      <span class="ci-price">${fmt(it.price * it.quantity)} ₽</span>
      <button class="ci-remove" data-action="cart-remove" data-id="${it.product_id}" aria-label="Убрать">✕</button>
    </div>`;
}

/* ---------- checkout ---------- */
function renderCheckout() {
  if (!state.cart.items.length) return show("cart");
  view.innerHTML = `
    <div class="section-title">Оформление заказа</div>
    <div class="detail-block">
      <div class="db-title">Ваш заказ</div>
      ${state.cart.items.map((it) => `<div class="db-row"><span class="k">${esc(it.name)} × ${it.quantity}</span><span class="v">${fmt(it.price * it.quantity)} ₽</span></div>`).join("")}
      <div class="db-row" style="margin-top:8px;padding-top:10px;border-top:1px solid var(--card-border)">
        <span class="k">Итого</span><span class="v" style="font-size:16px">${fmt(state.cart.total)} ₽</span>
      </div>
    </div>
    <div class="field"><label>Ваше имя</label><input id="coName" class="input" placeholder="Иван" value="${esc(state.me.first_name)}" autocomplete="off"></div>
    <div class="field"><label>Телефон</label><input id="coPhone" class="input" type="tel" placeholder="+7 900 000-00-00" autocomplete="tel"></div>
    <button class="btn btn-primary btn-block" data-action="submit-order">Подтвердить заказ</button>`;
}

async function submitOrder() {
  const name = $("#coName").value.trim();
  const phone = $("#coPhone").value.trim();
  if (!name) return toast("Введите имя", "err");
  if (!phone) return toast("Введите телефон", "err");
  try {
    buzz("success");
    const data = await api("/api/orders", { method: "POST", body: { name, phone } });
    state.cart = { items: [], total: 0, count: 0 };
    updateCartBadge();
    state.lastOrder = data.order;
    show("success");
  } catch (e) {
    toast(e.message, "err");
  }
}

function renderSuccess() {
  const o = state.lastOrder;
  view.innerHTML = `
    <div class="success">
      <div class="s-ico">✓</div>
      <h1>Заказ оформлен</h1>
      <div class="s-num">Заказ №${o.id} · ${o.created_at}</div>
      <div class="s-total">${fmt(o.total)} ₽</div>
      <p class="muted" style="margin:0">Мы свяжемся с вами в ближайшее время.</p>
      <button class="btn btn-primary btn-block" style="margin-top:22px" data-action="nav-catalog">Вернуться в каталог</button>
    </div>`;
  confetti();
}

/* ---------- orders ---------- */
async function renderOrders() {
  if (!state.orders.length) {
    view.innerHTML = `<div class="section-title">Мои заказы</div>` + orderSkeleton();
    try { state.orders = (await api("/api/orders")).orders; }
    catch (e) {
      view.innerHTML = `<div class="empty"><div class="e-ico">⚠️</div><div class="e-title">Не удалось загрузить заказы</div><p>${esc(e.message)}</p></div>`;
      return;
    }
  }
  if (!state.orders.length) {
    view.innerHTML = `
      <div class="empty">
        <div class="e-ico">📦</div>
        <div class="e-title">Заказов пока нет</div>
        <p>Оформите первый заказ в каталоге.</p>
        <button class="btn btn-primary" data-action="nav-catalog">В каталог</button>
      </div>`;
    return;
  }
  view.innerHTML = `
    <div class="section-title">Мои заказы</div>
    ${state.orders.map(orderRow).join("")}`;
}

function orderRow(o) {
  const st = STATUS[o.status] || STATUS.new;
  return `
    <div class="order-row" data-action="order-detail" data-id="${o.id}">
      <div>
        <div class="or-id">Заказ #${o.id}</div>
        <div class="or-meta">${o.created_at}</div>
      </div>
      <div class="or-right">
        <div class="or-price">${fmt(o.total)} ₽</div>
        <div class="or-meta" style="margin-top:4px"><span class="badge ${st.cls}">${st.label}</span></div>
      </div>
      <span class="or-chevron">›</span>
    </div>`;
}

/* ---------- admin ---------- */
async function renderAdmin() {
  if (!state.me.is_admin) return show("catalog");
  await loadAdminOrders();
  view.innerHTML = `
    <div class="section-title">Админ-панель</div>
    <div class="admin-tabs">${ADMIN_TABS.map(([val, label]) =>
      `<button class="atab ${state.adminFilter === val ? "active" : ""}" data-action="admin-filter" data-val="${val}">${label}</button>`).join("")}</div>
    ${state.adminOrders.length ? state.adminOrders.map(orderRow).join("") :
      `<div class="empty"><div class="e-ico">📭</div><div class="e-title">Заказов нет</div><p>В этом фильтре пока пусто.</p></div>`}`;
}

async function loadAdminOrders() {
  const q = state.adminFilter ? `?status=${state.adminFilter}` : "";
  try { state.adminOrders = (await api("/api/admin/orders" + q)).orders; } catch (e) { toast(e.message, "err"); }
}

async function renderAdminOrder() {
  let data;
  try {
    data = await api(`/api/admin/orders/${state.adminOrderId}`);
  } catch (e) {
    view.innerHTML = `<div class="empty"><div class="e-ico">⚠️</div><div class="e-title">Не удалось загрузить заказ</div><p>${esc(e.message)}</p></div>`;
    return;
  }
  const o = data.order;
  const items = data.items;
  const st = STATUS[o.status] || STATUS.new;
  view.innerHTML = `
    <div class="section-title">Заказ #${o.id} <span class="badge ${st.cls}">${st.label}</span></div>
    <div class="detail-block">
      <div class="db-row"><span class="k">Дата</span><span class="v">${o.created_at}</span></div>
      <div class="db-row"><span class="k">Клиент</span><span class="v">${esc(o.customer_name)}</span></div>
      <div class="db-row"><span class="k">Телефон</span><span class="v">${esc(o.phone)}</span></div>
      <div class="db-row"><span class="k">Сумма</span><span class="v">${fmt(o.total)} ₽</span></div>
    </div>
    <div class="detail-block">
      <div class="db-title">Состав заказа</div>
      ${items.map((it) => `<div class="db-row"><span class="k">${esc(it.product_name)} × ${it.quantity}</span><span class="v">${fmt(it.price * it.quantity)} ₽</span></div>`).join("")}
    </div>
    <div class="db-title">Статус</div>
    <div class="status-btns">${Object.entries(STATUS).map(([key, s]) =>
      `<button class="sbtn ${key === o.status ? "active" : ""}" data-action="set-status" data-id="${o.id}" data-status="${key}">${s.label}</button>`).join("")}</div>
    <button class="btn btn-primary btn-block" data-action="notify-status" data-id="${o.id}">Сообщить статус клиенту</button>
    <div class="notify-input">
      <input id="ntText" class="input" placeholder="Свой текст клиенту...">
      <button class="btn btn-ghost btn-sm" data-action="notify-text" data-id="${o.id}">Отправить</button>
    </div>`;
}

/* ---------- actions ---------- */
async function addToCart(productId, el) {
  try {
    const item = state.cart.items.find((i) => i.product_id === productId);
    const q = item ? item.quantity + 1 : 1;
    state.cart = await api("/api/cart/set", { method: "POST", body: { product_id: productId, quantity: q } });
    updateCartBadge();
    buzz();
    if (state.view === "catalog" && el?.classList.contains("btn-add")) flyToCart(el);
    toast("Товар добавлен в корзину");
    if (state.view === "product") renderProduct();
    else if (state.view === "catalog") renderCatalog();
  } catch (e) { toast(e.message, "err"); }
}

async function setQty(productId, q) {
  try {
    if (q < 0) q = 0;
    state.cart = await api("/api/cart/set", { method: "POST", body: { product_id: productId, quantity: q } });
    updateCartBadge();
    buzz();
    if (state.view === "cart") renderCart();
    else if (state.view === "product") renderProduct();
  } catch (e) { toast(e.message, "err"); }
}

async function clearCart() {
  try {
    state.cart = await api("/api/cart/clear", { method: "POST" });
    updateCartBadge();
    buzz();
    renderCart();
  } catch (e) { toast(e.message, "err"); }
}

async function changeStatus(orderId, status) {
  try {
    await api(`/api/admin/orders/${orderId}`, { method: "PATCH", body: { status } });
    buzz();
    toast("Статус обновлён");
    renderAdminOrder();
  } catch (e) { toast(e.message, "err"); }
}

async function notifyStatus(orderId) {
  try {
    await api(`/api/admin/orders/${orderId}/notify`, { method: "POST", body: { mode: "status" } });
    buzz();
    toast("Статус отправлен клиенту");
  } catch (e) { toast(e.message, "err"); }
}

async function notifyText(orderId) {
  const text = $("#ntText").value.trim();
  if (!text) return toast("Введите текст", "err");
  try {
    await api(`/api/admin/orders/${orderId}/notify`, { method: "POST", body: { mode: "text", text } });
    buzz();
    toast("Сообщение отправлено");
  } catch (e) { toast(e.message, "err"); }
}

/* ---------- event delegation ---------- */
const handlers = {
  cat: (d) => { state.categoryId = Number(d.id); buzz(); renderCatalog(); },
  product: (d) => { state.productId = Number(d.id); show("product"); },
  back: () => goBack(),
  "cart-add": (d, el) => addToCart(Number(d.id), el),
  qty: (d) => setQty(Number(d.id), Number(d.qty)),
  "cart-remove": (d) => setQty(Number(d.id), 0),
  "cart-clear": () => clearCart(),
  checkout: () => show("checkout"),
  "submit-order": () => submitOrder(),
  "order-detail": (d) => { if (state.me.is_admin) { state.adminOrderId = Number(d.id); show("admin-order"); } },
  "admin-filter": async (d) => { state.adminFilter = d.val; buzz(); await renderAdmin(); },
  "set-status": (d) => changeStatus(Number(d.id), d.status),
  "notify-status": (d) => notifyStatus(Number(d.id)),
  "notify-text": (d) => notifyText(Number(d.id)),
  "nav-catalog": () => show("catalog"),
  "nav-cart": () => show("cart"),
};

view.addEventListener("click", (e) => {
  const el = e.target.closest("[data-action]");
  if (!el) return;
  e.stopPropagation();
  const h = handlers[el.dataset.action];
  if (h) h(el.dataset, el);
});

$("#bottomNav").addEventListener("click", (e) => {
  const btn = e.target.closest(".nav-item");
  if (!btn || btn.classList.contains("hidden")) return;
  const name = btn.dataset.nav;
  if (name === "orders" && state.orders.length) state.orders = [];
  show(name);
});

document.addEventListener("keydown", (e) => {
  if (e.key !== "Backspace") return;
  const target = e.target;
  const typing =
    target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);
  if (typing) return;
  if (["product", "checkout", "admin-order"].includes(state.view)) goBack();
});

init();