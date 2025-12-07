document.addEventListener("DOMContentLoaded", function () {
  // 1. CẤU HÌNH GHN (Thay Token thật của bạn vào)
  const GHN_TOKEN = "TOKEN_THAT_CUA_BAN_O_DAY";
  const GHN_API_BASE =
    "https://dev-online-gateway.ghn.vn/shiip/public-api/master-data";

  const headers = { Token: GHN_TOKEN, "Content-Type": "application/json" };

  const callAPI = async (url, params = {}) => {
    try {
      const response = await axios.get(url, {
        headers: headers,
        params: params,
      });
      return response.data.code === 200 ? response.data.data : [];
    } catch (error) {
      console.error("API Error:", error);
      return [];
    }
  };

  const renderData = (dataList, selectId, codeField, nameField) => {
    const selectElement = document.querySelector("#" + selectId);
    if (!selectElement) return;
    let row = '<option value="">-- Chọn --</option>';
    if (Array.isArray(dataList)) {
      dataList.forEach((element) => {
        row += `<option data-code="${element[codeField]}" value="${element[nameField]}">${element[nameField]}</option>`;
      });
    }
    selectElement.innerHTML = row;
  };

  const loadProvinces = async () => {
    const data = await callAPI(GHN_API_BASE + "/province");
    if (data && data.length > 0) {
      data.sort((a, b) => a.ProvinceName.localeCompare(b.ProvinceName));
      renderData(data, "province", "ProvinceID", "ProvinceName");
    }
  };

  const loadDistricts = async (provinceId) => {
    const data = await callAPI(GHN_API_BASE + "/district", {
      province_id: provinceId,
    });
    renderData(data, "district", "DistrictID", "DistrictName");
  };

  const loadWards = async (districtId) => {
    const data = await callAPI(GHN_API_BASE + "/ward", {
      district_id: districtId,
    });
    renderData(data, "ward", "WardCode", "WardName");
  };

  // Sự kiện
  const provinceSelect = document.querySelector("#province");
  if (provinceSelect) {
    loadProvinces();
    provinceSelect.addEventListener("change", function () {
      const id = this.options[this.selectedIndex].getAttribute("data-code");
      document.querySelector("#province_id").value = id;
      document.querySelector("#district").innerHTML =
        '<option value="">-- Chọn Quận/Huyện --</option>';
      document.querySelector("#ward").innerHTML =
        '<option value="">-- Chọn Phường/Xã --</option>';
      if (id) loadDistricts(id);
    });
  }

  const districtSelect = document.querySelector("#district");
  if (districtSelect) {
    districtSelect.addEventListener("change", function () {
      const id = this.options[this.selectedIndex].getAttribute("data-code");
      document.querySelector("#district_id").value = id;
      document.querySelector("#ward").innerHTML =
        '<option value="">-- Chọn Phường/Xã --</option>';
      if (id) loadWards(id);
    });
  }

  const wardSelect = document.querySelector("#ward");
  if (wardSelect) {
    wardSelect.addEventListener("change", function () {
      const id = this.options[this.selectedIndex].getAttribute("data-code");
      document.querySelector("#ward_code").value = id;
    });
  }
});
