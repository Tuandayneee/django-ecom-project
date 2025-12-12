document.addEventListener("DOMContentLoaded", function () {
  // 1. CẤU HÌNH GHN (MÔI TRƯỜNG THẬT - PRODUCTION)
  const GHN_TOKEN = "4144ae8c-d3d8-11f0-9ba9-de592a7a61f0";
  const GHN_API_BASE =
    "https://online-gateway.ghn.vn/shiip/public-api/master-data";

  const headers = {
    Token: GHN_TOKEN,
    "Content-Type": "application/json",
  };

  // Hàm gọi API
  const callAPI = async (url, params = {}) => {
    try {
      const response = await axios.get(url, {
        headers: headers,
        params: params,
      });
      if (response.data.code === 200) {
        return response.data.data;
      } else {
        console.error("Lỗi GHN:", response.data.message);
        return [];
      }
    } catch (error) {
      console.error("Lỗi kết nối API:", error);
      return [];
    }
  };

  // Hàm hiển thị dữ liệu ra Select
  const renderData = (dataList, selectId, codeField, nameField) => {
    const selectElement = document.querySelector("#" + selectId);
    if (!selectElement) return;

    // Reset về mặc định
    let defaultText = selectElement.options[0].text;
    let row = `<option value="">${defaultText}</option>`;

    if (Array.isArray(dataList)) {
      dataList.forEach((element) => {
        row += `<option data-code="${element[codeField]}" value="${element[nameField]}">${element[nameField]}</option>`;
      });
    }
    selectElement.innerHTML = row;
  };

  // Hàm load Tỉnh
  const loadProvinces = async () => {
    const data = await callAPI(GHN_API_BASE + "/province");
    if (data && data.length > 0) {
      data.sort((a, b) => a.ProvinceName.localeCompare(b.ProvinceName));
      renderData(data, "province", "ProvinceID", "ProvinceName");
    }
  };

  // --- PHẦN BẠN ĐANG THIẾU: CÁC SỰ KIỆN CHANGE ---

  const provinceSelect = document.querySelector("#province");
  const districtSelect = document.querySelector("#district");
  const wardSelect = document.querySelector("#ward");

  // Chỉ chạy nếu tìm thấy ô chọn Tỉnh
  if (provinceSelect) {
    loadProvinces(); // Load tỉnh ngay khi vào trang

    // 1. SỰ KIỆN: Khi chọn Tỉnh -> Load Quận
    provinceSelect.addEventListener("change", async function () {
      // Lấy ID tỉnh từ thuộc tính data-code
      const selectedOption = this.options[this.selectedIndex];
      const provinceId = selectedOption.getAttribute("data-code");

      // Cập nhật input ẩn (để lưu vào DB)
      const inputId = document.querySelector("#province_id");
      if (inputId) inputId.value = provinceId || "";

      // Reset Quận và Xã về trạng thái ban đầu
      renderData([], "district", "DistrictID", "DistrictName");
      renderData([], "ward", "WardCode", "WardName");

      // Khóa hoặc Mở khóa ô Quận
      if (districtSelect) {
        districtSelect.disabled = true;
        if (provinceId) {
          // Gọi API lấy Quận
          const districts = await callAPI(GHN_API_BASE + "/district", {
            province_id: provinceId,
          });
          renderData(districts, "district", "DistrictID", "DistrictName");
          districtSelect.disabled = false; // Mở khóa
        }
      }

      if (wardSelect) wardSelect.disabled = true; // Khóa xã
      updateFullAddress(); // Cập nhật chuỗi hiển thị
    });
  }

  // 2. SỰ KIỆN: Khi chọn Quận -> Load Xã
  if (districtSelect) {
    districtSelect.addEventListener("change", async function () {
      const selectedOption = this.options[this.selectedIndex];
      const districtId = selectedOption.getAttribute("data-code");

      const inputId = document.querySelector("#district_id");
      if (inputId) inputId.value = districtId || "";

      // Reset Xã
      renderData([], "ward", "WardCode", "WardName");

      if (wardSelect) {
        wardSelect.disabled = true;
        if (districtId) {
          // Gọi API lấy Xã
          const wards = await callAPI(GHN_API_BASE + "/ward", {
            district_id: districtId,
          });
          renderData(wards, "ward", "WardCode", "WardName");
          wardSelect.disabled = false; // Mở khóa
        }
      }
      updateFullAddress();
    });
  }

  // 3. SỰ KIỆN: Khi chọn Xã -> Hoàn tất
  if (wardSelect) {
    wardSelect.addEventListener("change", function () {
      const selectedOption = this.options[this.selectedIndex];
      const wardId = selectedOption.getAttribute("data-code");

      const inputId = document.querySelector("#ward_code");
      if (inputId) inputId.value = wardId || "";

      updateFullAddress();
    });
  }

  // Hàm ghép chuỗi địa chỉ để hiển thị hoặc lưu vào field 'city' cũ
  const updateFullAddress = () => {
    const p = document.querySelector("#province");
    const d = document.querySelector("#district");
    const w = document.querySelector("#ward");
    const fullAddrInput = document.querySelector("#full_address_str");

    if (p && d && w && fullAddrInput) {
      // Chỉ cập nhật khi cả 3 ô đã được chọn
      if (p.value && d.value && w.value) {
        fullAddrInput.value = `${w.value}, ${d.value}, ${p.value}`;
      }
    }
  };
});
