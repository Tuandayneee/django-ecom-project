document.addEventListener("DOMContentLoaded", function () {
  // 1. Dùng API esgoo.net (Ổn định hơn open-api)
  const PROVINCE_API = "https://esgoo.net/api-tinhthanh/1/0.htm";
  const DISTRICT_API = "https://esgoo.net/api-tinhthanh/2/";
  const WARD_API = "https://esgoo.net/api-tinhthanh/3/";

  const provinceSelect = document.getElementById("province");
  const districtSelect = document.getElementById("district");
  const wardSelect = document.getElementById("ward");

  // Các ô Input Ẩn (Lưu tên để gửi về Django)
  const cityNameInput = document.getElementById("city_name");
  const districtNameInput = document.getElementById("district_name");
  const wardNameInput = document.getElementById("ward_name");

  // Hàm gọi API
  async function fetchLocation(url) {
    try {
      const response = await fetch(url);
      const data = await response.json();
      if (data.error === 0) return data.data;
      return [];
    } catch (error) {
      console.error("Lỗi API:", error);
      return [];
    }
  }

  // Hàm render Option
  function renderOptions(array, selectElement, defaultText) {
    let html = `<option value="">-- ${defaultText} --</option>`;
    array.forEach((item) => {
      // Lưu tên vào data-name để dễ lấy
      html += `<option value="${item.id}" data-name="${item.full_name}">${item.full_name}</option>`;
    });
    selectElement.innerHTML = html;
    selectElement.disabled = false;
  }

  // 2. Load Tỉnh khi vào trang
  fetchLocation(PROVINCE_API).then((data) =>
    renderOptions(data, provinceSelect, "Tỉnh/Thành")
  );

  // 3. Sự kiện chọn Tỉnh
  provinceSelect.addEventListener("change", function () {
    districtSelect.innerHTML = '<option value="">-- Quận/Huyện --</option>';
    wardSelect.innerHTML = '<option value="">-- Phường/Xã --</option>';
    districtSelect.disabled = true;
    wardSelect.disabled = true;

    // LẤY TÊN TỈNH -> Gán vào Input Ẩn
    const selectedOption = this.options[this.selectedIndex];
    const name = selectedOption.getAttribute("data-name");
    if (cityNameInput) cityNameInput.value = name || "";

    // Reset huyện/xã
    if (districtNameInput) districtNameInput.value = "";
    if (wardNameInput) wardNameInput.value = "";

    if (this.value) {
      fetchLocation(`${DISTRICT_API}${this.value}.htm`).then((data) =>
        renderOptions(data, districtSelect, "Quận/Huyện")
      );
    }
  });

  // 4. Sự kiện chọn Huyện
  districtSelect.addEventListener("change", function () {
    wardSelect.innerHTML = '<option value="">-- Phường/Xã --</option>';
    wardSelect.disabled = true;

    // LẤY TÊN HUYỆN -> Gán vào Input Ẩn
    const selectedOption = this.options[this.selectedIndex];
    const name = selectedOption.getAttribute("data-name");
    if (districtNameInput) districtNameInput.value = name || "";

    if (wardNameInput) wardNameInput.value = "";

    if (this.value) {
      fetchLocation(`${WARD_API}${this.value}.htm`).then((data) =>
        renderOptions(data, wardSelect, "Phường/Xã")
      );
    }
  });

  // 5. Sự kiện chọn Xã (QUAN TRỌNG)
  wardSelect.addEventListener("change", function () {
    // LẤY TÊN XÃ -> Gán vào Input Ẩn
    const selectedOption = this.options[this.selectedIndex];
    const name = selectedOption.getAttribute("data-name");
    if (wardNameInput) wardNameInput.value = name || "";
  });
});
