/**
 * common.js - Utility functions and shared logic for all pages
 * Follows senior-level coding standards with proper documentation
 */

/**
 * Format currency in Vietnamese Dong
 * @param {number} amount - The amount to format
 * @returns {string} Formatted currency string
 */
function formatMoney(amount) {
  return Number(amount).toLocaleString("vi-VN").replace(/\./g, ",") + " đ";
}

/**
 * Format currency using Intl API (alternative)
 * @param {number} amount - The amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
  return new Intl.NumberFormat("vi-VN").format(amount) + " đ";
}

/**
 * Safe DOM element selector with error handling
 * @param {string} selector - CSS selector
 * @returns {Element|null} DOM element or null
 */
function safeSelectorOne(selector) {
  try {
    return document.querySelector(selector);
  } catch (e) {
    console.error("Invalid selector:", selector, e);
    return null;
  }
}

/**
 * Safe DOM elements selector with error handling
 * @param {string} selector - CSS selector
 * @returns {NodeList} DOM elements collection
 */
function safeSelectorAll(selector) {
  try {
    return document.querySelectorAll(selector);
  } catch (e) {
    console.error("Invalid selector:", selector, e);
    return [];
  }
}

/**
 * Make fetch request with error handling
 * @param {string} url - Endpoint URL
 * @param {object} options - Fetch options
 * @returns {Promise} Fetch promise
 */
async function safeFetch(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken") || "",
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response;
  } catch (error) {
    console.error("Fetch error:", error);
    throw error;
  }
}

/**
 * Get CSRF token from cookies
 * @param {string} name - Cookie name
 * @returns {string} Cookie value
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * Debounce function for optimizing event listeners
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, delay = 300) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

/**
 * Throttle function for optimizing event listeners
 * @param {Function} func - Function to throttle
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, delay = 300) {
  let lastCall = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      func.apply(this, args);
    }
  };
}

/**
 * Show loading state on button
 * @param {Element} btn - Button element
 * @param {string} loadingText - Text to show while loading
 */
function showButtonLoading(btn, loadingText = "Đang xử lý...") {
  if (!btn) return;
  btn.dataset.originalText = btn.innerHTML;
  btn.innerHTML = `<i class="fa fa-spinner fa-spin"></i> ${loadingText}`;
  btn.disabled = true;
}

/**
 * Hide loading state on button
 * @param {Element} btn - Button element
 */
function hideButtonLoading(btn) {
  if (!btn || !btn.dataset.originalText) return;
  btn.innerHTML = btn.dataset.originalText;
  btn.disabled = false;
}

/**
 * Show alert message to user
 * @param {string} message - Message to display
 * @param {string} type - Alert type (success, danger, warning, info)
 */
function showAlert(message, type = "danger") {
  console.log(`[${type.toUpperCase()}] ${message}`);
  alert(message); // Can be replaced with custom toast notification
}

/**
 * Scroll to element smoothly
 * @param {Element|string} target - Element or selector
 * @param {object} options - Scroll options
 */
function scrollToElement(target, options = {}) {
  let element = target;
  if (typeof target === "string") {
    element = document.querySelector(target);
  }

  if (element) {
    element.scrollIntoView({
      behavior: options.behavior || "smooth",
      block: options.block || "start",
      inline: options.inline || "nearest",
    });
  }
}

/**
 * Initialize tooltips (Bootstrap tooltips)
 */
function initializeTooltips() {
  const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltips.forEach((tooltipElement) => {
    new bootstrap.Tooltip(tooltipElement);
  });
}

/**
 * Add active class to element and remove from siblings
 * @param {Element} element - Element to make active
 * @param {string} selector - Selector for all items
 * @param {string} activeClass - Active class name (default: 'active')
 */
function setActiveElement(element, selector, activeClass = "active") {
  document.querySelectorAll(selector).forEach((el) => {
    el.classList.remove(activeClass);
  });
  element?.classList.add(activeClass);
}

/**
 * Disable element with visual feedback
 * @param {Element} element - Element to disable
 * @param {string} reason - Reason for disabling (shown as title)
 */
function disableElement(element, reason = "") {
  if (!element) return;
  element.classList.add("disabled");
  element.style.pointerEvents = "none";
  element.style.opacity = "0.6";
  if (reason) element.title = reason;
}

/**
 * Enable element
 * @param {Element} element - Element to enable
 */
function enableElement(element) {
  if (!element) return;
  element.classList.remove("disabled");
  element.style.pointerEvents = "auto";
  element.style.opacity = "1";
  element.title = "";
}

/**
 * Initialize common event listeners and utilities
 * Call this in DOMContentLoaded event
 */
document.addEventListener("DOMContentLoaded", function () {
  // Prevent dropdown menu from closing on click
  document.addEventListener("click", function (e) {
    if (e.target.closest(".dropdown-menu")) {
      e.stopPropagation();
    }
  });

  // Initialize tooltips
  if (typeof bootstrap !== "undefined") {
    initializeTooltips();
  }

  console.log("✓ Common utilities initialized");
});
