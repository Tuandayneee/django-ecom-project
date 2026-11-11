// public/static/js/pages/checkout.js

document.addEventListener("DOMContentLoaded", function () {
  // 1. LẤY CONFIG TỪ HTML
  const config = window.CheckoutConfig || {};

  // Nếu thiếu config quan trọng thì dừng
  if (!config.urls || !config.csrfToken) {
    console.warn("CheckoutConfig missing. Logic checkout disabled.");
    return;
  }

  // 2. LẤY CÁC ELEMENT
  const addressRadios = document.querySelectorAll(
    'input[name="selected_address"]'
  );
  const shippingElem = document.getElementById("shipping-fee-display");
  const totalElem = document.getElementById("total-display");
  const loadingOverlay = document.getElementById("summaryLoading");
  const noAddressFlag = document.getElementById("no_address_flag");

  // --- HÀM HỖ TRỢ ---
  const formatCurrency = (amount) =>
    new Intl.NumberFormat("vi-VN").format(amount) + " đ";

  // --- LOGIC CẬP NHẬT PHÍ SHIP (AJAX) ---
  function updateShippingFee(addressUid) {
    if (!addressUid) return;

    // Bật Loading
    if (loadingOverlay) loadingOverlay.style.display = "flex";

    fetch(config.urls.updateShipping, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": config.csrfToken,
      },
      body: JSON.stringify({ address_uid: addressUid }),
    })
      .then((response) => response.json())
      .then((data) => {
        // Delay giả lập nhẹ (300ms) để user thấy hiệu ứng loading
        setTimeout(() => {
          if (loadingOverlay) loadingOverlay.style.display = "none";

          if (data.status === "success") {
            // Cập nhật hiển thị phí ship
            if (shippingElem) {
              if (data.shipping_fee > 0) {
                shippingElem.innerText = `+ ${formatCurrency(
                  data.shipping_fee
                )}`;
                shippingElem.className = ""; // Reset class màu (nếu có)
              } else {
                shippingElem.innerHTML =
                  '<span class="text-success">Miễn phí</span>';
              }
            }

            // Cập nhật Tổng tiền cuối cùng
            if (totalElem) {
              totalElem.innerText = formatCurrency(data.total);
            }
          } else {
            console.error("Lỗi tính phí:", data.message);
            // Có thể alert lỗi cho user biết
          }
        }, 300);
      })
      .catch((error) => {
        console.error("Lỗi mạng:", error);
        if (loadingOverlay) loadingOverlay.style.display = "none";
      });
  }

  // --- SỰ KIỆN ---

  // 1. Khi chọn địa chỉ khác -> Gọi API tính lại phí
  addressRadios.forEach((radio) => {
    radio.addEventListener("change", function () {
      updateShippingFee(this.value);
    });
  });

  // 2. Logic tự động chọn địa chỉ đầu tiên nếu chưa chọn
  if (addressRadios.length > 0) {
    const checkedRadio = document.querySelector(
      'input[name="selected_address"]:checked'
    );
    if (!checkedRadio) {
      // Chưa chọn cái nào -> Chọn cái đầu tiên & Update phí
      addressRadios[0].checked = true;
      updateShippingFee(addressRadios[0].value);
    }
  }

  // 3. Auto show modal nếu chưa có địa chỉ nào
  if (noAddressFlag && typeof bootstrap !== "undefined") {
    const modalEl = document.getElementById("addAddressModal");
    if (modalEl) {
      var myModal = new bootstrap.Modal(modalEl);
      myModal.show();
    }
  }
});
