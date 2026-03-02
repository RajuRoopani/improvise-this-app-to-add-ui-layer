/**
 * app.js — DoorDash SPA frontend logic
 * Hash-based routing, API integration, cart management, order tracking.
 * User is hardcoded to "user1" (only supported user on the backend).
 */

'use strict';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const USER_ID = 'user1';
const API_BASE = '/api';

// Order status progression for simulate button
const STATUS_PROGRESSION = ['confirmed', 'preparing', 'out_for_delivery', 'delivered'];

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const state = {
  currentRestaurant: null,   // full restaurant object currently viewed
  currentOrderId: null,      // order_id currently being tracked
  cart: null,                // latest cart object from backend
  lastRestaurantId: null,    // for back-to-restaurant from cart
  searchDebounceTimer: null,
};

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------

function fmt(amount) {
  return `$${Number(amount).toFixed(2)}`;
}

function esc(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// ---------------------------------------------------------------------------
// Toast notifications
// ---------------------------------------------------------------------------

function showToast(message, type = 'success', duration = 3000) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `
    <span class="toast__icon">${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
    <span class="toast__message">${esc(message)}</span>
  `;
  container.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => toast.classList.add('toast--visible'));

  // Auto-dismiss
  setTimeout(() => {
    toast.classList.remove('toast--visible');
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
  }, duration);
}

// ---------------------------------------------------------------------------
// Section routing — show/hide page sections
// ---------------------------------------------------------------------------

const SECTIONS = ['home-section', 'restaurant-section', 'cart-section', 'order-tracking-section'];

function showSection(id) {
  SECTIONS.forEach(sId => {
    const el = document.getElementById(sId);
    if (el) el.hidden = (sId !== id);
  });
}

// ---------------------------------------------------------------------------
// Hash router
// ---------------------------------------------------------------------------

function parseHash() {
  const hash = window.location.hash.replace('#', '') || 'home';
  if (hash === 'home' || hash === '') return { page: 'home' };
  if (hash === 'cart') return { page: 'cart' };
  const restaurantMatch = hash.match(/^restaurant\/(.+)$/);
  if (restaurantMatch) return { page: 'restaurant', id: restaurantMatch[1] };
  const trackingMatch = hash.match(/^tracking\/(.+)$/);
  if (trackingMatch) return { page: 'tracking', orderId: trackingMatch[1] };
  return { page: 'home' };
}

async function handleRoute() {
  const route = parseHash();

  // Always refresh cart badge on navigation
  await refreshCartState();

  switch (route.page) {
    case 'home':
      showSection('home-section');
      await loadRestaurants();
      break;
    case 'restaurant':
      showSection('restaurant-section');
      await loadRestaurantMenu(route.id);
      break;
    case 'cart':
      showSection('cart-section');
      await renderCartPage();
      break;
    case 'tracking':
      showSection('order-tracking-section');
      await renderTrackingPage(route.orderId);
      break;
    default:
      window.location.hash = '#home';
  }
}

// ---------------------------------------------------------------------------
// Cart state — kept in sync throughout the session
// ---------------------------------------------------------------------------

async function refreshCartState() {
  try {
    const resp = await fetch(`${API_BASE}/cart/${USER_ID}`);
    if (!resp.ok) throw new Error(`Cart fetch failed: ${resp.status}`);
    state.cart = await resp.json();
    updateCartBadge(state.cart);
  } catch (e) {
    console.error('refreshCartState error:', e);
    // On failure keep whatever we had
  }
}

function updateCartBadge(cart) {
  const badge = document.getElementById('cart-count-badge');
  const summaryBar = document.getElementById('cart-summary-bar');
  const barCount = document.getElementById('cart-bar-count');
  const barTotal = document.getElementById('cart-bar-total');

  const totalItems = cart && cart.items
    ? cart.items.reduce((sum, item) => sum + item.quantity, 0)
    : 0;

  if (badge) badge.textContent = totalItems;

  if (summaryBar) {
    if (totalItems > 0) {
      summaryBar.hidden = false;
      if (barCount) barCount.textContent = `${totalItems} item${totalItems !== 1 ? 's' : ''}`;
      if (barTotal) barTotal.textContent = fmt(cart.total);
    } else {
      summaryBar.hidden = true;
    }
  }
}

// ---------------------------------------------------------------------------
// HOME — load & render restaurants
// ---------------------------------------------------------------------------

async function loadRestaurants(cuisineFilter = null, searchQuery = null) {
  const grid = document.getElementById('restaurant-grid');
  const emptyState = document.getElementById('empty-state-restaurants');

  // Build query string
  const params = new URLSearchParams();
  if (cuisineFilter && cuisineFilter !== 'All') params.set('cuisine', cuisineFilter);
  if (searchQuery && searchQuery.trim()) params.set('search', searchQuery.trim());

  try {
    const resp = await fetch(`${API_BASE}/restaurants?${params}`);
    if (!resp.ok) throw new Error(`Restaurants fetch failed: ${resp.status}`);
    const restaurants = await resp.json();

    grid.innerHTML = '';
    if (restaurants.length === 0) {
      emptyState.hidden = false;
      return;
    }
    emptyState.hidden = true;
    restaurants.forEach(r => grid.insertAdjacentHTML('beforeend', renderRestaurantCard(r)));
  } catch (e) {
    console.error('loadRestaurants error:', e);
    showToast('Failed to load restaurants. Please try again.', 'error');
  }
}

function renderRestaurantCard(r) {
  const fee = r.delivery_fee === 0 ? 'Free delivery' : `${fmt(r.delivery_fee)} delivery`;
  return `
    <article
      class="restaurant-card"
      role="listitem"
      tabindex="0"
      data-restaurant-id="${esc(r.id)}"
      aria-label="${esc(r.name)}"
    >
      <div class="restaurant-card__img-wrap">
        <img
          class="restaurant-card__img"
          src="${esc(r.image_url)}"
          alt="${esc(r.name)}"
          loading="lazy"
          onerror="this.src='https://picsum.photos/seed/${esc(r.id)}/400/300'"
        />
      </div>
      <div class="restaurant-card__body">
        <h3 class="restaurant-card__name">${esc(r.name)}</h3>
        <p class="restaurant-card__desc">${esc(r.description)}</p>
        <div class="restaurant-card__meta">
          <span class="restaurant-meta-item">⭐ ${r.rating}</span>
          <span class="restaurant-meta-item">⏱ ${esc(r.delivery_time)}</span>
          <span class="restaurant-meta-item">🚚 ${fee}</span>
          <span class="restaurant-meta-item">🍽 ${esc(r.cuisine_type)}</span>
        </div>
      </div>
    </article>
  `;
}

// Cuisine filter pill logic
function initCuisineFilters() {
  const container = document.getElementById('cuisine-filters');
  if (!container) return;

  container.addEventListener('click', e => {
    const btn = e.target.closest('[data-cuisine]');
    if (!btn) return;

    // Update active state
    container.querySelectorAll('[data-cuisine]').forEach(b => {
      b.classList.remove('cuisine-pill--active');
      b.setAttribute('aria-pressed', 'false');
    });
    btn.classList.add('cuisine-pill--active');
    btn.setAttribute('aria-pressed', 'true');

    const cuisine = btn.dataset.cuisine;
    const search = document.getElementById('search-input')?.value || '';
    loadRestaurants(cuisine === 'All' ? null : cuisine, search);
  });
}

// Search input with debounce
function initSearch() {
  const input = document.getElementById('search-input');
  if (!input) return;

  input.addEventListener('input', () => {
    clearTimeout(state.searchDebounceTimer);
    state.searchDebounceTimer = setTimeout(() => {
      const activeCuisine = document.querySelector('.cuisine-pill--active')?.dataset.cuisine || 'All';
      loadRestaurants(activeCuisine === 'All' ? null : activeCuisine, input.value);
    }, 300);
  });
}

// Restaurant card click → navigate
function initRestaurantGridClicks() {
  const grid = document.getElementById('restaurant-grid');
  if (!grid) return;

  grid.addEventListener('click', e => {
    const card = e.target.closest('[data-restaurant-id]');
    if (!card) return;
    const id = card.dataset.restaurantId;
    state.lastRestaurantId = id;
    window.location.hash = `#restaurant/${id}`;
  });

  // Keyboard accessible
  grid.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') {
      const card = e.target.closest('[data-restaurant-id]');
      if (!card) return;
      e.preventDefault();
      card.click();
    }
  });
}

// ---------------------------------------------------------------------------
// RESTAURANT DETAIL — load menu
// ---------------------------------------------------------------------------

async function loadRestaurantMenu(restaurantId) {
  const headerEl = document.getElementById('restaurant-header');
  const menuContainer = document.getElementById('menu-container');
  const loadingEl = document.getElementById('menu-loading');

  // Show loading spinner, clear old content
  if (loadingEl) loadingEl.hidden = false;
  menuContainer.querySelectorAll('.menu-category').forEach(el => el.remove());

  try {
    // Fetch restaurant details and menu in parallel
    const [restResp, menuResp] = await Promise.all([
      fetch(`${API_BASE}/restaurants/${restaurantId}`),
      fetch(`${API_BASE}/restaurants/${restaurantId}/menu`),
    ]);

    if (!restResp.ok) throw new Error(`Restaurant not found: ${restResp.status}`);
    if (!menuResp.ok) throw new Error(`Menu not found: ${menuResp.status}`);

    const restaurant = await restResp.json();
    const menuItems = await menuResp.json();

    state.currentRestaurant = restaurant;
    state.lastRestaurantId = restaurantId;

    // Render restaurant header
    const fee = restaurant.delivery_fee === 0 ? 'Free delivery' : `${fmt(restaurant.delivery_fee)} delivery`;
    headerEl.innerHTML = `
      <img
        class="restaurant-header__hero"
        src="${esc(restaurant.image_url)}"
        alt="${esc(restaurant.name)}"
        onerror="this.src='https://picsum.photos/seed/${esc(restaurantId)}/800/300'"
      />
      <div class="restaurant-header__info">
        <h2 class="restaurant-header__name">${esc(restaurant.name)}</h2>
        <p class="restaurant-header__desc">${esc(restaurant.description)}</p>
        <div class="restaurant-header__meta">
          <span class="restaurant-meta-item">⭐ ${restaurant.rating}</span>
          <span class="restaurant-meta-item">⏱ ${esc(restaurant.delivery_time)}</span>
          <span class="restaurant-meta-item">🚚 ${fee}</span>
          <span class="restaurant-meta-item">📍 ${esc(restaurant.cuisine_type)}</span>
        </div>
      </div>
    `;

    // Group menu items by category (preserve insertion order)
    const categories = {};
    menuItems.forEach(item => {
      if (!categories[item.category]) categories[item.category] = [];
      categories[item.category].push(item);
    });

    // Render grouped menu sections
    const categoryOrder = ['Mains', 'Appetizers', 'Sides', 'Desserts', 'Drinks'];
    const orderedKeys = [
      ...categoryOrder.filter(c => categories[c]),
      ...Object.keys(categories).filter(c => !categoryOrder.includes(c)),
    ];

    const fragments = orderedKeys.map(cat => renderMenuCategory(cat, categories[cat]));
    fragments.forEach(html => menuContainer.insertAdjacentHTML('beforeend', html));

    if (loadingEl) loadingEl.hidden = true;
  } catch (e) {
    console.error('loadRestaurantMenu error:', e);
    if (loadingEl) loadingEl.hidden = true;
    menuContainer.insertAdjacentHTML('beforeend', `
      <p class="menu-error">Failed to load menu. <a href="#home">Go back</a></p>
    `);
    showToast('Failed to load restaurant menu.', 'error');
  }
}

function renderMenuCategory(categoryName, items) {
  const itemsHtml = items.map(item => renderMenuItem(item)).join('');
  return `
    <section class="menu-category">
      <h3 class="menu-category__title">${esc(categoryName)}</h3>
      <div class="menu-category__items">
        ${itemsHtml}
      </div>
    </section>
  `;
}

function renderMenuItem(item) {
  return `
    <div class="menu-item" data-item-id="${esc(item.id)}">
      <div class="menu-item__info">
        <h4 class="menu-item__name">${esc(item.name)}</h4>
        <p class="menu-item__desc">${esc(item.description)}</p>
        <span class="menu-item__price">${fmt(item.price)}</span>
      </div>
      <div class="menu-item__img-wrap">
        <img
          class="menu-item__img"
          src="${esc(item.image_url)}"
          alt="${esc(item.name)}"
          loading="lazy"
          onerror="this.src='https://picsum.photos/seed/${esc(item.id)}/300/200'"
        />
        <button
          class="btn btn--add menu-item__add-btn"
          data-item-id="${esc(item.id)}"
          data-item-name="${esc(item.name)}"
          aria-label="Add ${esc(item.name)} to cart"
        >
          + Add
        </button>
      </div>
    </div>
  `;
}

// Add to cart handler — delegated on menu-container
function initMenuAddToCart() {
  const menuContainer = document.getElementById('menu-container');
  if (!menuContainer) return;

  menuContainer.addEventListener('click', async e => {
    const btn = e.target.closest('.menu-item__add-btn');
    if (!btn) return;

    const itemId = btn.dataset.itemId;
    const itemName = btn.dataset.itemName;

    // Optimistic UI: disable button during request
    btn.disabled = true;
    btn.textContent = '...';

    try {
      const resp = await fetch(`${API_BASE}/cart/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID, menu_item_id: itemId, quantity: 1 }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }

      const cart = await resp.json();
      state.cart = cart;
      updateCartBadge(cart);
      showToast(`${itemName} added to cart!`, 'success');
    } catch (e) {
      console.error('addToCart error:', e);
      showToast(`Could not add item: ${e.message}`, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = '+ Add';
    }
  });
}

// ---------------------------------------------------------------------------
// CART PAGE — render, update quantity, remove, place order
// ---------------------------------------------------------------------------

async function renderCartPage() {
  // Always fetch fresh cart data
  await refreshCartState();
  const cart = state.cart;

  const cartItemsEl = document.getElementById('cart-items');
  const emptyCartEl = document.getElementById('empty-state-cart');
  const addressSection = document.getElementById('cart-address-section');
  const orderSummary = document.getElementById('order-summary');
  const placeOrderBtn = document.getElementById('place-order-btn');

  if (!cart || cart.items.length === 0) {
    // Empty cart view
    cartItemsEl.innerHTML = '';
    cartItemsEl.hidden = true;
    if (emptyCartEl) emptyCartEl.hidden = false;
    if (addressSection) addressSection.hidden = true;
    if (orderSummary) orderSummary.hidden = true;
    return;
  }

  // Cart has items
  if (emptyCartEl) emptyCartEl.hidden = true;
  cartItemsEl.hidden = false;
  if (addressSection) addressSection.hidden = false;
  if (orderSummary) orderSummary.hidden = false;

  // Render cart items
  cartItemsEl.innerHTML = cart.items.map(item => renderCartItem(item)).join('');

  // Update totals
  document.getElementById('cart-subtotal').textContent = fmt(cart.subtotal);
  document.getElementById('cart-delivery-fee').textContent = fmt(cart.delivery_fee);
  document.getElementById('cart-tax').textContent = fmt(cart.tax);
  document.getElementById('cart-total').textContent = fmt(cart.total);

  // Enable place order button if address is filled
  syncPlaceOrderBtn();
}

function renderCartItem(item) {
  return `
    <div class="cart-item" role="listitem" data-item-id="${esc(item.menu_item_id)}">
      <div class="cart-item__info">
        <span class="cart-item__name">${esc(item.name)}</span>
        <span class="cart-item__price">${fmt(item.price)} each</span>
      </div>
      <div class="cart-item__controls">
        <button
          class="qty-btn qty-btn--minus"
          data-item-id="${esc(item.menu_item_id)}"
          aria-label="Decrease quantity of ${esc(item.name)}"
        >−</button>
        <span class="qty-value" aria-label="Quantity: ${item.quantity}">${item.quantity}</span>
        <button
          class="qty-btn qty-btn--plus"
          data-item-id="${esc(item.menu_item_id)}"
          aria-label="Increase quantity of ${esc(item.name)}"
        >+</button>
        <button
          class="cart-item__remove"
          data-item-id="${esc(item.menu_item_id)}"
          aria-label="Remove ${esc(item.name)} from cart"
        >🗑</button>
      </div>
      <span class="cart-item__total">${fmt(item.item_total)}</span>
    </div>
  `;
}

function syncPlaceOrderBtn() {
  const btn = document.getElementById('place-order-btn');
  const addrInput = document.getElementById('delivery-address-input');
  if (!btn || !addrInput) return;
  btn.disabled = !addrInput.value.trim();
}

// Cart quantity / remove event delegation
function initCartItemEvents() {
  const cartItemsEl = document.getElementById('cart-items');
  if (!cartItemsEl) return;

  cartItemsEl.addEventListener('click', async e => {
    const minusBtn = e.target.closest('.qty-btn--minus');
    const plusBtn = e.target.closest('.qty-btn--plus');
    const removeBtn = e.target.closest('.cart-item__remove');

    if (minusBtn) {
      const itemId = minusBtn.dataset.itemId;
      const currentQty = getItemQty(itemId);
      if (currentQty <= 1) {
        await removeCartItem(itemId);
      } else {
        await updateCartItem(itemId, currentQty - 1);
      }
    } else if (plusBtn) {
      const itemId = plusBtn.dataset.itemId;
      const currentQty = getItemQty(itemId);
      await updateCartItem(itemId, currentQty + 1);
    } else if (removeBtn) {
      const itemId = removeBtn.dataset.itemId;
      await removeCartItem(itemId);
    }
  });
}

function getItemQty(itemId) {
  if (!state.cart) return 1;
  const found = state.cart.items.find(i => i.menu_item_id === itemId);
  return found ? found.quantity : 1;
}

async function updateCartItem(itemId, newQty) {
  try {
    const resp = await fetch(`${API_BASE}/cart/${USER_ID}/items/${itemId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity: newQty }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    state.cart = await resp.json();
    updateCartBadge(state.cart);
    await renderCartPage();
  } catch (e) {
    console.error('updateCartItem error:', e);
    showToast('Could not update item quantity.', 'error');
  }
}

async function removeCartItem(itemId) {
  try {
    const resp = await fetch(`${API_BASE}/cart/${USER_ID}/items/${itemId}`, {
      method: 'DELETE',
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    state.cart = await resp.json();
    updateCartBadge(state.cart);
    await renderCartPage();
    showToast('Item removed from cart.', 'info');
  } catch (e) {
    console.error('removeCartItem error:', e);
    showToast('Could not remove item.', 'error');
  }
}

// ---------------------------------------------------------------------------
// PLACE ORDER
// ---------------------------------------------------------------------------

function initPlaceOrderBtn() {
  const btn = document.getElementById('place-order-btn');
  const addrInput = document.getElementById('delivery-address-input');
  const addrError = document.getElementById('address-error');

  if (!btn || !addrInput) return;

  // Enable/disable as user types
  addrInput.addEventListener('input', () => {
    syncPlaceOrderBtn();
    if (addrInput.value.trim() && addrError) addrError.hidden = true;

    // Update navbar address display while typing
    const navAddrText = document.getElementById('navbar-address-text');
    if (navAddrText && addrInput.value.trim()) {
      navAddrText.textContent = addrInput.value.trim();
    }
  });

  btn.addEventListener('click', async () => {
    const address = addrInput.value.trim();

    if (!address) {
      if (addrError) addrError.hidden = false;
      addrInput.focus();
      return;
    }
    if (addrError) addrError.hidden = true;

    // Validate cart still has items
    if (!state.cart || state.cart.items.length === 0) {
      showToast('Your cart is empty.', 'error');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Placing order…';

    try {
      const resp = await fetch(`${API_BASE}/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID, delivery_address: address }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }

      const order = await resp.json();
      state.currentOrderId = order.order_id;

      // Cart is now empty on the backend — clear local state
      state.cart = {
        user_id: USER_ID,
        restaurant_id: null,
        items: [],
        subtotal: 0.0,
        delivery_fee: 0.0,
        tax: 0.0,
        total: 0.0,
      };
      updateCartBadge(state.cart);

      showToast('Order placed! 🎉', 'success', 4000);

      // Navigate to tracking
      window.location.hash = `#tracking/${order.order_id}`;
    } catch (e) {
      console.error('placeOrder error:', e);
      showToast(`Order failed: ${e.message}`, 'error');
      btn.disabled = false;
      btn.textContent = 'Place Order';
    }
  });
}

// ---------------------------------------------------------------------------
// ORDER TRACKING
// ---------------------------------------------------------------------------

async function renderTrackingPage(orderId) {
  state.currentOrderId = orderId;

  const trackingIdEl = document.getElementById('tracking-order-id');
  const orderDetailsEl = document.getElementById('order-details');

  if (trackingIdEl) {
    trackingIdEl.textContent = `#DD-${orderId.slice(0, 8).toUpperCase()}`;
  }

  try {
    const resp = await fetch(`${API_BASE}/orders/${USER_ID}/${orderId}`);
    if (!resp.ok) throw new Error(`Order not found: ${resp.status}`);
    const order = await resp.json();

    renderOrderStatus(order.status);
    renderOrderDetails(order, orderDetailsEl);
  } catch (e) {
    console.error('renderTrackingPage error:', e);
    if (orderDetailsEl) {
      orderDetailsEl.innerHTML = `<p class="order-error">Could not load order details.</p>`;
    }
    showToast('Failed to load order details.', 'error');
  }
}

const STATUS_STEP_INDEX = {
  confirmed: 0,
  preparing: 1,
  out_for_delivery: 2,
  delivered: 3,
};

function renderOrderStatus(status) {
  const steps = document.querySelectorAll('#order-status-progress .order-step');
  const fill = document.getElementById('order-track-fill');

  const currentIndex = STATUS_STEP_INDEX[status] ?? 0;
  const totalSteps = steps.length;

  steps.forEach((step, i) => {
    step.classList.remove('order-step--active', 'order-step--complete');
    if (i < currentIndex) {
      step.classList.add('order-step--complete');
    } else if (i === currentIndex) {
      step.classList.add('order-step--active');
    }
  });

  // Track fill: 0% at step 0, 100% at last step
  const fillPct = totalSteps > 1 ? (currentIndex / (totalSteps - 1)) * 100 : 0;
  if (fill) fill.style.width = `${fillPct}%`;
}

function renderOrderDetails(order, container) {
  if (!container) return;

  const itemsHtml = order.items.map(item => `
    <div class="order-details__item">
      <span>${esc(item.name)} × ${item.quantity}</span>
      <span>${fmt(item.item_total)}</span>
    </div>
  `).join('');

  container.innerHTML = `
    <div class="order-details__from">
      <strong>From:</strong> ${esc(order.restaurant_name)}
    </div>
    <div class="order-details__address">
      <strong>Delivering to:</strong> ${esc(order.delivery_address)}
    </div>
    <div class="order-details__items">
      ${itemsHtml}
    </div>
    <div class="order-details__totals">
      <div class="order-details__total-row">
        <span>Subtotal</span><span>${fmt(order.subtotal)}</span>
      </div>
      <div class="order-details__total-row">
        <span>Delivery Fee</span><span>${fmt(order.delivery_fee)}</span>
      </div>
      <div class="order-details__total-row">
        <span>Tax</span><span>${fmt(order.tax)}</span>
      </div>
      <div class="order-details__total-row order-details__total-row--grand">
        <span><strong>Total</strong></span><span><strong>${fmt(order.total)}</strong></span>
      </div>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// SIMULATE PROGRESS button
// ---------------------------------------------------------------------------

function initSimulateProgress() {
  const btn = document.getElementById('simulate-progress-btn');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    if (!state.currentOrderId) {
      showToast('No active order to simulate.', 'error');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Updating…';

    try {
      // Fetch current order to find next status
      const resp = await fetch(`${API_BASE}/orders/${USER_ID}/${state.currentOrderId}`);
      if (!resp.ok) throw new Error(`Order fetch failed: ${resp.status}`);
      const order = await resp.json();

      const currentIdx = STATUS_PROGRESSION.indexOf(order.status);
      if (currentIdx === -1 || currentIdx >= STATUS_PROGRESSION.length - 1) {
        showToast('Order is already delivered! 🎉', 'info');
        btn.disabled = true;
        btn.textContent = 'Delivered ✓';
        return;
      }

      const nextStatus = STATUS_PROGRESSION[currentIdx + 1];

      const updateResp = await fetch(`${API_BASE}/orders/${state.currentOrderId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus }),
      });

      if (!updateResp.ok) {
        const err = await updateResp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${updateResp.status}`);
      }

      const updatedOrder = await updateResp.json();
      renderOrderStatus(updatedOrder.status);

      const statusLabels = {
        confirmed: 'Order confirmed!',
        preparing: 'Restaurant is preparing your order.',
        out_for_delivery: 'Your order is out for delivery!',
        delivered: 'Your order has been delivered! Enjoy! 🎉',
      };
      showToast(statusLabels[updatedOrder.status] || `Status: ${updatedOrder.status}`, 'success');

      if (updatedOrder.status === 'delivered') {
        btn.disabled = true;
        btn.textContent = 'Delivered ✓';
      } else {
        btn.disabled = false;
        btn.textContent = 'Simulate Progress';
      }
    } catch (e) {
      console.error('simulateProgress error:', e);
      showToast(`Could not advance order: ${e.message}`, 'error');
      btn.disabled = false;
      btn.textContent = 'Simulate Progress';
    }
  });
}

// ---------------------------------------------------------------------------
// BACK BUTTONS and NAVIGATION
// ---------------------------------------------------------------------------

function initBackButtons() {
  // Back to home from restaurant detail
  const backToHomeBtn = document.getElementById('back-to-home-btn');
  if (backToHomeBtn) {
    backToHomeBtn.addEventListener('click', () => {
      window.location.hash = '#home';
    });
  }

  // Back to restaurant from cart
  const backToRestaurantBtn = document.getElementById('back-to-restaurant-btn');
  if (backToRestaurantBtn) {
    backToRestaurantBtn.addEventListener('click', () => {
      if (state.lastRestaurantId) {
        window.location.hash = `#restaurant/${state.lastRestaurantId}`;
      } else {
        window.location.hash = '#home';
      }
    });
  }

  // Back to home from order tracking ("Order Again")
  const backFromTrackingBtn = document.getElementById('back-to-home-from-tracking');
  if (backFromTrackingBtn) {
    backFromTrackingBtn.addEventListener('click', () => {
      state.currentOrderId = null;
      window.location.hash = '#home';
    });
  }

  // Browse restaurants button (empty cart state)
  const browseBtn = document.getElementById('browse-restaurants-btn');
  if (browseBtn) {
    browseBtn.addEventListener('click', () => {
      window.location.hash = '#home';
    });
  }

  // Navbar cart button
  const navCartBtn = document.getElementById('navbar-cart-btn');
  if (navCartBtn) {
    navCartBtn.addEventListener('click', () => {
      window.location.hash = '#cart';
    });
  }

  // Cart summary bar click → go to cart
  const summaryBar = document.getElementById('cart-summary-bar');
  if (summaryBar) {
    summaryBar.addEventListener('click', () => {
      window.location.hash = '#cart';
    });
    summaryBar.style.cursor = 'pointer';
  }

  // Navbar logo click → home
  const logoEl = document.querySelector('.navbar__logo');
  if (logoEl) {
    logoEl.style.cursor = 'pointer';
    logoEl.addEventListener('click', () => {
      window.location.hash = '#home';
    });
  }
}

// ---------------------------------------------------------------------------
// APP INIT
// ---------------------------------------------------------------------------

function init() {
  // Wire up all event listeners
  initCuisineFilters();
  initSearch();
  initRestaurantGridClicks();
  initMenuAddToCart();
  initCartItemEvents();
  initPlaceOrderBtn();
  initSimulateProgress();
  initBackButtons();

  // Handle hash changes (browser back/forward)
  window.addEventListener('hashchange', handleRoute);

  // Initial route
  handleRoute();
}

// Boot when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
