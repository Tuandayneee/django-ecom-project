/**
 * Logic cho trang chi tiết sản phẩm
 * Đọc dữ liệu từ window.ProductConfig được khai báo trong HTML
 */

document.addEventListener("DOMContentLoaded", function () {
  const config = window.ProductConfig || {};
  const variantsMap = config.variantsMap || {};

  const els = {
    priceDisplay: document.getElementById("productPrice"),
    originalPriceDisplay: document.getElementById("originalPriceDisplay"),
    saleBadge: document.getElementById("saleBadge"),
    saleBadgeText: document.getElementById("saleBadgeText"),
    stockDisplay: document.getElementById("productStock"),
    addToCartBtn: document.getElementById("addToCartBtn"),
    variantInput: document.getElementById("addToCartVariantInput"),
    qtyHiddenInput: document.getElementById("addToCartQtyInput"),
    quantityInput: document.getElementById("quantityInput"),
    mainImg: document.getElementById("mainImage"),
  };

  window.changeImage = function (element, src, colorId) {
    if (els.mainImg && src) {
      if (!els.mainImg.src.includes(src)) {
        els.mainImg.style.opacity = "0.5";
        setTimeout(() => {
          els.mainImg.src = src;
          els.mainImg.style.opacity = "1";
        }, 150);
      }

      if (element) {
        document
          .querySelectorAll(".thumb-item")
          .forEach((el) => el.classList.remove("active-thumb"));
        element.classList.add("active-thumb");
      }
    }

    colorId = colorId ? colorId.toString().trim() : "";
    if (colorId && colorId !== "None") {
      const colorInput = document.querySelector(
        `input[name="color"][value="${colorId}"]`
      );
      if (colorInput) {
        colorInput.checked = true;
        updateVariantState(false);
      }
    }
  };

  function updateVariantState(shouldUpdateImage = true) {
    const colorEl = document.querySelector('input[name="color"]:checked');
    const sizeEl = document.querySelector('input[name="size"]:checked');

    if (!sizeEl || !colorEl) return;

    const colorId = colorEl.value;
    const sizeId = sizeEl.value;
    const qty = Math.max(1, parseInt(els.quantityInput?.value) || 1);

    const key = `${colorId}-${sizeId}`;
    const data = variantsMap[key];

    if (data) {
      if (shouldUpdateImage && data.image_url && els.mainImg) {
        if (!els.mainImg.src.includes(data.image_url)) {
          els.mainImg.style.opacity = "0.5";
          setTimeout(() => {
            els.mainImg.src = data.image_url;
            els.mainImg.style.opacity = "1";
          }, 150);
        }
      }

      const totalPrice = data.price * qty;
      if (els.priceDisplay)
        els.priceDisplay.innerText = formatMoney(totalPrice);

      if (els.originalPriceDisplay) {
        const totalOriginal = data.original_price * qty;

        if (data.original_price > data.price) {
          els.originalPriceDisplay.innerText = formatMoney(totalOriginal);
          els.originalPriceDisplay.style.display = "inline-block";

          if (els.saleBadge) {
            const percent = Math.round(
              ((data.original_price - data.price) / data.original_price) * 100
            );
            els.saleBadge.style.display = "inline-block";
            if (els.saleBadgeText) els.saleBadgeText.innerText = `-${percent}%`;
          }
        } else {
          els.originalPriceDisplay.style.display = "none";
          if (els.saleBadge) els.saleBadge.style.display = "none";
        }
      }

      if (els.variantInput) els.variantInput.value = data.variant_uid;
      if (els.qtyHiddenInput) els.qtyHiddenInput.value = qty;

      if (data.stock > 0) {
        els.stockDisplay.innerHTML = `<span class="text-success fw-bold"><i class="fa fa-check"></i> Còn hàng (Kho: ${data.stock})</span>`;
        els.addToCartBtn.classList.remove("disabled");
        els.addToCartBtn.disabled = false;
        els.addToCartBtn.innerText = "Thêm vào giỏ";
        els.addToCartBtn.style.pointerEvents = "auto";

        if (qty > data.stock) {
          els.addToCartBtn.classList.add("disabled");
          els.addToCartBtn.disabled = true;
          els.stockDisplay.innerHTML = `<span class="text-danger fw-bold">Không đủ hàng (Còn ${data.stock})</span>`;
        }
      } else {
        els.stockDisplay.innerHTML = `<span class="text-danger fw-bold"><i class="fa fa-times"></i> Hết hàng</span>`;
        els.addToCartBtn.classList.add("disabled");
        els.addToCartBtn.disabled = true;
        els.addToCartBtn.innerText = "Hết hàng";
        els.addToCartBtn.style.pointerEvents = "none";
      }
    } else {
      els.stockDisplay.innerHTML = `<span class="text-muted">Tùy chọn không khả dụng</span>`;
      els.addToCartBtn.classList.add("disabled");
      els.addToCartBtn.disabled = true;
      if (els.variantInput) els.variantInput.value = "";
    }
  }

  function formatMoney(amount) {
    return Number(amount).toLocaleString("vi-VN") + " đ";
  }

  window.changeQty = function (delta) {
    if (!els.quantityInput) return;

    let currentQty = parseInt(els.quantityInput.value) || 1;
    let newQty = currentQty + delta;
    if (newQty < 1) newQty = 1;

    els.quantityInput.value = newQty;
    updateVariantState(false);
  };

  window.scrollToReview = function () {
    const reviewSec = document.getElementById("reviewSection");
    if (reviewSec) reviewSec.scrollIntoView({ behavior: "smooth" });
  };

  const INITIAL_VISIBLE_COUNT = 3;
  let currentFilter = "all";
  let isExpanded = false;

  renderReviews();

  window.toggleReviews = function () {
    isExpanded = !isExpanded;

    const btn = document.getElementById("loadMoreReviewsBtn");
    const reviewList = document.querySelector(".review-list");

    if (isExpanded) {
      if (btn) btn.innerText = "Rút gọn";
    } else {
      if (btn) btn.innerText = "Xem tất cả đánh giá";
      if (reviewList)
        reviewList.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    renderReviews();
  };

  window.filterReviews = function (rating, btnElement) {
    document.querySelectorAll(".filter-btn").forEach((btn) => {
      btn.classList.remove("active", "btn-dark", "text-white");
      btn.classList.add("btn-outline-dark");
    });
    if (btnElement) {
      btnElement.classList.remove("btn-outline-dark");
      btnElement.classList.add("active", "btn-dark", "text-white");
    }

    currentFilter = rating;
    isExpanded = false;

    const btn = document.getElementById("loadMoreReviewsBtn");
    if (btn) btn.innerText = "Xem tất cả đánh giá";

    renderReviews();
  };

  function renderReviews() {
    const allReviews = document.querySelectorAll(".review-item");
    const btnLoadMore = document.getElementById("loadMoreReviewsBtn");
    const msgNoReview = document.getElementById("noReviewMsg");

    let countMatched = 0;
    let countShown = 0;
    const limit = isExpanded ? 99999 : INITIAL_VISIBLE_COUNT;

    allReviews.forEach((item) => {
      const itemRating = parseFloat(item.getAttribute("data-rating"));
      const isMatch =
        currentFilter === "all" || Math.floor(itemRating) == currentFilter;

      if (isMatch) {
        countMatched++;

        if (countShown < limit) {
          item.classList.remove("d-none");
          countShown++;
        } else {
          item.classList.add("d-none");
        }
      } else {
        item.classList.add("d-none");
      }
    });

    if (btnLoadMore) {
      if (countMatched > INITIAL_VISIBLE_COUNT) {
        btnLoadMore.classList.remove("d-none");
        btnLoadMore.style.display = "inline-block";
        btnLoadMore.innerText = isExpanded ? "Rút gọn" : "Xem tất cả đánh giá";
      } else {
        btnLoadMore.classList.add("d-none");
        btnLoadMore.style.display = "none";
      }
    }

    if (msgNoReview) {
      if (countMatched === 0) msgNoReview.classList.remove("d-none");
      else msgNoReview.classList.add("d-none");
    }
  }

  window.buyNow = function () {
    const colorEl = document.querySelector('input[name="color"]:checked');
    const sizeEl = document.querySelector('input[name="size"]:checked');

    if (!colorEl || !sizeEl) {
      alert("Vui lòng chọn Màu sắc và Kích thước!");
      return;
    }

    const colorId = colorEl.value;
    const sizeId = sizeEl.value;
    const key = `${colorId}-${sizeId}`;
    const data = variantsMap[key];
    const qty = parseInt(els.quantityInput?.value) || 1;

    if (!data || qty < 1 || data.stock < qty) {
      alert("Sản phẩm tạm hết hàng hoặc số lượng không đủ!");
      return;
    }

    const buyBtn = document.getElementById("buyNowBtn");
    const originalText = buyBtn.innerHTML;

    buyBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Đang xử lý...';
    buyBtn.disabled = true;

    fetch(config.urls.buyNow, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": config.csrfToken,
      },
      body: JSON.stringify({ variant_uid: data.variant_uid, quantity: qty }),
    })
      .then((r) => r.json())
      .then((res) => {
        if (res.status === "success") {
          window.location.href = config.urls.checkout;
        } else {
          alert(res.message || "Có lỗi xảy ra");
          buyBtn.innerHTML = originalText;
          buyBtn.disabled = false;
        }
      })
      .catch((e) => {
        console.error(e);
        alert("Lỗi kết nối đến server");
        buyBtn.innerHTML = originalText;
        buyBtn.disabled = false;
      });
  };

  document.querySelectorAll(".variant-selector").forEach((el) => {
    el.addEventListener("change", () => updateVariantState(true));
  });

  if (els.quantityInput) {
    els.quantityInput.addEventListener("change", () => changeQty(0));
  }
});
