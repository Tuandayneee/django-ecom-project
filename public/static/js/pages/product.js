/**
 * Logic cho trang chi tiết sản phẩm
 * Đọc dữ liệu từ window.ProductConfig được khai báo trong HTML
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. LẤY CONFIG TỪ HTML
  const config = window.ProductConfig || {};

  // Kiểm tra dữ liệu an toàn
  const variantsMap = config.variantsMap || {};

  // Lấy các element giao diện
  const els = {
    priceDisplay: document.getElementById("productPrice"),
    originalPriceDisplay: document.getElementById("originalPriceDisplay"),
    saleBadge: document.getElementById("saleBadge"),
    saleBadgeText: document.getElementById("saleBadgeText"),
    stockDisplay: document.getElementById("productStock"),
    addToCartBtn: document.getElementById("addToCartBtn"),
    quantityInput: document.getElementById("quantityInput"),
    mainImg: document.getElementById("mainImage"),
  };

  console.log("Product JS Loaded.");

  // --- 2. CÁC HÀM LOGIC ---

  // Gắn vào window để gọi được từ onclick
  window.changeImage = function (element, src, colorId) {
    // A. Đổi ảnh chính
    if (els.mainImg && src) {
      // Chỉ đổi nếu src khác nhau để tránh nháy ảnh
      if (!els.mainImg.src.includes(src)) {
        els.mainImg.style.opacity = "0.5";
        setTimeout(() => {
          els.mainImg.src = src;
          els.mainImg.style.opacity = "1";
        }, 150);
      }

      // Active border cho thumbnail
      if (element) {
        document
          .querySelectorAll(".thumb-item")
          .forEach((el) => el.classList.remove("active-thumb"));
        element.classList.add("active-thumb");
      }
    }

    // B. Tự động chọn Màu (nếu click vào ảnh biến thể màu)
    colorId = colorId ? colorId.toString().trim() : "";
    if (colorId && colorId !== "None") {
      const colorInput = document.querySelector(
        `input[name="color"][value="${colorId}"]`
      );
      if (colorInput) {
        colorInput.checked = true;
        updateVariantState(false); // Update logic nhưng không cần đổi lại ảnh
      }
    }
  };

  function updateVariantState(shouldUpdateImage = true) {
    const colorEl = document.querySelector('input[name="color"]:checked');
    const sizeEl = document.querySelector('input[name="size"]:checked');

    // Nếu thiếu 1 trong 2 tùy chọn thì chưa tính toán variant
    if (!sizeEl || !colorEl) return;

    const colorId = colorEl.value;
    const sizeId = sizeEl.value;
    const qty = parseInt(els.quantityInput?.value) || 1;

    // Tạo key để tra cứu trong variantsMap
    const key = `${colorId}-${sizeId}`;
    const data = variantsMap[key];

    if (data) {
      // A. XỬ LÝ ẢNH
      if (shouldUpdateImage && data.image_url && els.mainImg) {
        if (!els.mainImg.src.includes(data.image_url)) {
          els.mainImg.style.opacity = "0.5";
          setTimeout(() => {
            els.mainImg.src = data.image_url;
            els.mainImg.style.opacity = "1";
          }, 150);
        }
      }

      // B. XỬ LÝ GIÁ
      const totalPrice = data.price * qty;
      if (els.priceDisplay)
        els.priceDisplay.innerText = formatMoney(totalPrice);

      // C. XỬ LÝ SALE (Giá gốc & Badge)
      if (els.originalPriceDisplay) {
        const totalOriginal = data.original_price * qty;

        if (data.original_price > data.price) {
          // Có giảm giá
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
          // Không giảm giá
          els.originalPriceDisplay.style.display = "none";
          if (els.saleBadge) els.saleBadge.style.display = "none";
        }
      }

      // D. XỬ LÝ KHO & LINK ADD TO CART
      if (data.stock > 0) {
        els.stockDisplay.innerHTML = `<span class="text-success fw-bold"><i class="fa fa-check"></i> Còn hàng (Kho: ${data.stock})</span>`;
        els.addToCartBtn.classList.remove("disabled");
        els.addToCartBtn.innerText = "Thêm vào giỏ";
        els.addToCartBtn.style.pointerEvents = "auto";

        // Cập nhật URL thêm vào giỏ
        els.addToCartBtn.href = `${config.urls.addToCart}?variant=${data.variant_uid}&quantity=${qty}`;

        // Kiểm tra nếu mua quá số lượng kho
        if (qty > data.stock) {
          els.addToCartBtn.classList.add("disabled");
          els.addToCartBtn.href = "javascript:void(0)";
          els.stockDisplay.innerHTML = `<span class="text-danger fw-bold">Không đủ hàng (Còn ${data.stock})</span>`;
        }
      } else {
        // Hết hàng
        els.stockDisplay.innerHTML = `<span class="text-danger fw-bold"><i class="fa fa-times"></i> Hết hàng</span>`;
        els.addToCartBtn.classList.add("disabled");
        els.addToCartBtn.innerText = "Hết hàng";
        els.addToCartBtn.href = "javascript:void(0)";
        els.addToCartBtn.style.pointerEvents = "none";
      }
    } else {
      // Không tìm thấy variant (Combination không tồn tại)
      els.stockDisplay.innerHTML = `<span class="text-muted">Tùy chọn không khả dụng</span>`;
      els.addToCartBtn.classList.add("disabled");
      els.addToCartBtn.href = "javascript:void(0)";
    }
  }

  // --- HELPER FUNCTIONS ---

  // Format tiền Việt: 1000000 => 1.000.000 đ
  function formatMoney(amount) {
    return Number(amount).toLocaleString("vi-VN") + " đ";
  }

  window.changeQty = function (delta) {
    if (!els.quantityInput) return;

    let currentQty = parseInt(els.quantityInput.value) || 1;
    let newQty = currentQty + delta;
    if (newQty < 1) newQty = 1;

    els.quantityInput.value = newQty;
    updateVariantState(false); // Cập nhật lại giá tổng nhưng không đổi ảnh
  };

  window.scrollToReview = function () {
    const reviewSec = document.getElementById("reviewSection");
    if (reviewSec) reviewSec.scrollIntoView({ behavior: "smooth" });
  };

  // ============================================================
  // --- LOGIC REVIEW (ĐÃ FIX LAYOUT) ---
  // ============================================================

  const INITIAL_VISIBLE_COUNT = 3;
  let currentFilter = "all";
  let isExpanded = false;

  // Render lần đầu khi trang load
  renderReviews();

  // Hàm lọc review (được gọi từ HTML onclick)
  window.toggleReviews = function () {
    isExpanded = !isExpanded; // Đảo ngược trạng thái

    const btn = document.getElementById("loadMoreReviewsBtn");
    const reviewList = document.querySelector(".review-list");

    if (isExpanded) {
      // TRẠNG THÁI MỞ RỘNG
      if (btn) btn.innerText = "Rút gọn";
    } else {
      // TRẠNG THÁI RÚT GỌN
      if (btn) btn.innerText = "Xem tất cả đánh giá";

      // (Tùy chọn) Cuộn nhẹ lên đầu danh sách review khi rút gọn cho dễ nhìn
      if (reviewList)
        reviewList.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    renderReviews(); // Vẽ lại giao diện
  };

  // Hàm hiển thị TẤT CẢ
  window.filterReviews = function (rating, btnElement) {
    // ... (Code xử lý style nút filter giữ nguyên như cũ) ...
    document.querySelectorAll(".filter-btn").forEach((btn) => {
      btn.classList.remove("active", "btn-dark", "text-white");
      btn.classList.add("btn-outline-dark");
    });
    if (btnElement) {
      btnElement.classList.remove("btn-outline-dark");
      btnElement.classList.add("active", "btn-dark", "text-white");
    }

    // Khi lọc, reset trạng thái về "Gọn"
    currentFilter = rating;
    isExpanded = false;

    // Reset chữ trên nút về "Xem tất cả"
    const btn = document.getElementById("loadMoreReviewsBtn");
    if (btn) btn.innerText = "Xem tất cả đánh giá";

    renderReviews();
  };

  function renderReviews() {
    const allReviews = document.querySelectorAll(".review-item");
    const btnLoadMore = document.getElementById("loadMoreReviewsBtn");
    const msgNoReview = document.getElementById("noReviewMsg");

    let countMatched = 0; // Tổng số bài khớp bộ lọc
    let countShown = 0; // Số bài được hiển thị ra

    // Xác định giới hạn hiển thị dựa trên trạng thái
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

    // --- XỬ LÝ NÚT BẤM (QUAN TRỌNG) ---
    if (btnLoadMore) {
      // Nút chỉ hiện khi Tổng số bài tìm thấy > Số bài mặc định (3 bài)
      if (countMatched > INITIAL_VISIBLE_COUNT) {
        btnLoadMore.classList.remove("d-none");
        btnLoadMore.style.display = "inline-block";

        // Cập nhật text nút (đề phòng trường hợp F5 hoặc logic khác)
        btnLoadMore.innerText = isExpanded ? "Rút gọn" : "Xem tất cả đánh giá";
      } else {
        // Nếu chỉ có <= 3 bài thì ẩn nút luôn
        btnLoadMore.classList.add("d-none");
        btnLoadMore.style.display = "none";
      }
    }

    // Xử lý thông báo không có review
    if (msgNoReview) {
      if (countMatched === 0) msgNoReview.classList.remove("d-none");
      else msgNoReview.classList.add("d-none");
    }
  }

  // ============================================================
  // --- LOGIC MUA NGAY (BUY NOW) ---
  // ============================================================

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

    if (!data || data.stock < qty) {
      alert("Sản phẩm tạm hết hàng hoặc số lượng không đủ!");
      return;
    }

    const buyBtn = document.getElementById("buyNowBtn");
    const originalText = buyBtn.innerHTML;

    // UI Loading
    buyBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Đang xử lý...';
    buyBtn.disabled = true;

    // Gọi API
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

  // --- EVENT LISTENERS ---

  // Lắng nghe sự kiện thay đổi radio button (Màu/Size)
  document.querySelectorAll(".variant-selector").forEach((el) => {
    el.addEventListener("change", () => updateVariantState(true));
  });

  // Lắng nghe thay đổi input số lượng
  if (els.quantityInput) {
    els.quantityInput.addEventListener("change", () => changeQty(0));
  }
});
