// public/static/js/pages/cart.js

document.addEventListener("DOMContentLoaded", function () {
  // 1. LẤY CẤU HÌNH TỪ HTML
  const config = window.CartConfig || {};

  // Kiểm tra xem có config chưa, nếu chưa thì dừng (tránh lỗi ở các trang khác)
  if (!config.urls || !config.csrfToken) {
    console.warn("CartConfig chưa được khai báo. Bỏ qua logic giỏ hàng.");
    return;
  }

  // --- CÁC HÀM HỖ TRỢ ---
  function formatCurrency(amount) {
    return new Intl.NumberFormat("vi-VN").format(amount) + " đ";
  }

  // --- LOGIC CẬP NHẬT GIỎ HÀNG ---
  function updateCartItem(uid, qty, inputElem, btnElem, rowElem) {
    // Sử dụng URL từ Config
    fetch(config.urls.updateCart, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": config.csrfToken, // Token từ Config
      },
      body: JSON.stringify({ item_uid: uid, new_quantity: qty }),
    })
      .then((response) => response.json())
      .then((data) => {
        // Mở khóa nút và dòng
        btnElem.disabled = false;
        rowElem.style.opacity = "1";

        if (data.status === "Success") {
          // Cập nhật giá trị input và data-old-value
          inputElem.value = qty;
          inputElem.dataset.oldValue = qty;

          // Cập nhật Tổng tiền sản phẩm (Thành tiền)
          const itemTotalElem = document.getElementById(`item-total-${uid}`);
          if (itemTotalElem)
            itemTotalElem.innerText = formatCurrency(data.item_total);

          // Cập nhật Tổng giỏ hàng (Subtotal & Total)
          const subTotalElem = document.getElementById(`cart-subtotal`);
          const cartTotalElem = document.getElementById(`cart-total`);

          if (subTotalElem)
            subTotalElem.innerText = formatCurrency(data.subtotal);
          if (cartTotalElem)
            cartTotalElem.innerText = formatCurrency(data.cart_total);

          // Cập nhật Giảm giá (nếu có)
          const discountElem = document.getElementById(`cart-discount`);
          if (discountElem && data.discount) {
            discountElem.innerText = `-${formatCurrency(data.discount)}`;
          }
        } else {
          alert(data.message || "Lỗi cập nhật giỏ hàng");
          // Reset về giá trị cũ nếu lỗi
          if (inputElem.dataset.oldValue) {
            inputElem.value = inputElem.dataset.oldValue;
          }
        }
      })
      .catch((err) => {
        console.error(err);
        btnElem.disabled = false;
        rowElem.style.opacity = "1";
        alert("Đã xảy ra lỗi kết nối");
      });
  }

  // --- SỰ KIỆN CLICK NÚT TĂNG/GIẢM ---
  const buttons = document.querySelectorAll(".btn-update");

  buttons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const uid = this.dataset.uid;
      const action = this.dataset.action;
      const input = document.getElementById(`qty-${uid}`);

      if (!input) return;

      let currentQty = parseInt(input.value) || 0;
      let newQty = currentQty;

      if (action === "increase") newQty++;
      if (action === "decrease") newQty--;

      if (newQty < 1) return;

      // UI Feedback: Làm mờ dòng đang sửa
      const row = document.getElementById(`row-${uid}`);
      if (row) row.style.opacity = "0.5";
      this.disabled = true;

      // Gọi hàm update
      updateCartItem(uid, newQty, input, this, row);
    });
  });
});
