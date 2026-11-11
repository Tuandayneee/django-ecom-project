// public/static/js/pages/auth.js

document.addEventListener("DOMContentLoaded", function () {
  // 1. LẤY CẤU HÌNH TỪ HTML
  const config = window.AuthConfig || { isRegister: false };

  // 2. LẤY CÁC ELEMENT
  const container = document.getElementById("container");
  const signUpBtn = document.getElementById("signUp");
  const signInBtn = document.getElementById("signIn");
  const mobileToSignup = document.getElementById("to-signup");
  const mobileToSignin = document.getElementById("to-signin");

  // Kiểm tra nếu không có container thì dừng (tránh lỗi ở trang khác)
  if (!container) return;

  // --- CÁC HÀM XỬ LÝ ---

  // Hàm chuyển sang Đăng ký
  function activateSignUp() {
    container.classList.add("right-panel-active");
  }

  // Hàm chuyển sang Đăng nhập
  function activateSignIn() {
    container.classList.remove("right-panel-active");
  }

  // --- SỰ KIỆN CLICK ---

  // Desktop Buttons
  if (signUpBtn) signUpBtn.addEventListener("click", activateSignUp);
  if (signInBtn) signInBtn.addEventListener("click", activateSignIn);

  // Mobile Links
  if (mobileToSignup) mobileToSignup.addEventListener("click", activateSignUp);
  if (mobileToSignin) mobileToSignin.addEventListener("click", activateSignIn);

  if (config.isRegister) {
    activateSignUp();
  }
});
