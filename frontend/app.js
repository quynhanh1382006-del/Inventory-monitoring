const $ = (selector) => document.querySelector(selector);
const money = (value) =>
  new Intl.NumberFormat("vi-VN", {
    style: "currency", currency: "VND", maximumFractionDigits: 0
  }).format(Number(value || 0));

let productsCache = [];
let categoriesCache = [];
let suppliersCache = [];
let messageTimer;

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Yêu cầu thất bại");
  return data;
}

function showMessage(text, isError = false) {
  const box = $("#message");
  box.textContent = text;
  box.classList.toggle("error", isError);
  box.classList.remove("hidden");
  clearTimeout(messageTimer);
  messageTimer = setTimeout(() => box.classList.add("hidden"), 4000);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;",
    '"': "&quot;", "'": "&#39;"
  })[char]);
}

function emptyRow(columns, message = "Chưa có dữ liệu") {
  return `<tr><td colspan="${columns}">${escapeHtml(message)}</td></tr>`;
}
async function loadDashboard() {
  const data = await api("/api/dashboard");

  $("#total-products").textContent = data.total_products;
  $("#total-quantity").textContent =
    Number(data.total_quantity).toLocaleString("vi-VN");
  $("#low-stock").textContent = data.low_stock;
  $("#stock-value").textContent = money(data.stock_value);

  const products = await api("/api/products");

  $("#dashboard-products").innerHTML =
    products.slice(0, 8).map(p => {
      const isLow = Number(p.quantity) <= Number(p.min_stock);

      return `
        <tr>
          <td>${escapeHtml(p.code)}</td>
          <td>${escapeHtml(p.name)}</td>
          <td>${escapeHtml(p.category_name)}</td>
          <td>${Number(p.quantity).toLocaleString("vi-VN")}
              ${escapeHtml(p.unit)}</td>
          <td>
            <span class="pill ${isLow ? "warning" : ""}">
              ${isLow ? "Sắp hết hàng" : "Còn hàng"}
            </span>
          </td>
        </tr>`;
    }).join("") || emptyRow(5);

  const lowStockProducts = products.filter(
    p => Number(p.quantity) <= Number(p.min_stock)
  );

  $("#low-stock-products").innerHTML =
  lowStockProducts.map(p => {
    const quantity = Number(p.quantity);
    const minStock = Number(p.min_stock);
    const needed = Math.max(0, minStock - quantity);

    return `
      <tr>
        <td>${escapeHtml(p.code)}</td>
        <td>${escapeHtml(p.name)}</td>
        <td>${quantity.toLocaleString("vi-VN")}
            ${escapeHtml(p.unit)}</td>
        <td>${minStock.toLocaleString("vi-VN")}
            ${escapeHtml(p.unit)}</td>
        <td>
          <strong>${needed.toLocaleString("vi-VN")}
            ${escapeHtml(p.unit)}</strong>
        </td>
        <td>
          <span class="pill warning">Cần kiểm tra</span>
        </td>
      </tr>
    `;
  }).join("") || emptyRow(6, "Không có sản phẩm sắp hết hàng");
}

async function loadProducts(keyword = "") {
  productsCache = await api(`/api/products?q=${encodeURIComponent(keyword)}`);
  $("#products-table").innerHTML = productsCache.map(p => `    <tr>      <td>${escapeHtml(p.code)}</td>
      <td>${escapeHtml(p.name)}</td>
      <td>${escapeHtml(p.category_name)}</td>
      <td>${escapeHtml(p.unit)}</td>
      <td>${Number(p.quantity).toLocaleString("vi-VN")}</td>
      <td>${money(p.import_price)}</td>
      <td>${money(p.sale_price)}</td>
      <td>
        <button class="action-button edit" data-edit="${p.id}">Sửa</button>
        <button class="action-button delete" data-delete="${p.id}">Xóa</button>
      </td>
    </tr>`).join("") || emptyRow(8, "Không tìm thấy sản phẩm");
  renderProductSelects();
}

function renderProductSelects() {
  const options = productsCache.map(p =>
    `<option value="${p.id}">${escapeHtml(p.code)} — ${escapeHtml(p.name)} (tồn: ${p.quantity})</option>`
  ).join("");
  document.querySelectorAll(".product-select").forEach(select => {
    select.innerHTML = options || '<option value="">Chưa có sản phẩm</option>';
  });
}

async function loadCategories() {
  categoriesCache = await api("/api/categories");
  $("#category-select").innerHTML = categoriesCache.map(c =>
    `<option value="${c.id}">${escapeHtml(c.name)}</option>`
  ).join("");
}

async function loadSuppliers() {
  suppliersCache = await api("/api/suppliers");
  $("#supplier-select").innerHTML = suppliersCache.map(s =>
    `<option value="${s.id}">${escapeHtml(s.name)}</option>`
  ).join("");
}


async function loadHistory() {
  const params = new URLSearchParams();
const type = $("#history-type")?.value || "all";
const from = $("#history-from")?.value || "";
const to = $("#history-to")?.value || "";

params.set("type", type === "Nhập kho" ? "import" :
                    type === "Xuất kho" ? "export" : "all");

if (from) params.set("start_date", from);
if (to) params.set("end_date", to);
  const query = params.toString();
  const rows = await api(
    "/api/history" + (query ? `?${query}` : "")
  );

  $("#history-table").innerHTML = rows.map(row => `
    <tr>
      <td>${escapeHtml(row.code)}</td>
      <td>
        <span class="pill ${row.type === "Xuất kho" ? "warning" : ""}">
          ${escapeHtml(row.type)}
        </span>
      </td>
      <td>${escapeHtml(row.created_at)}</td>
      <td>${escapeHtml(row.product_name)}</td>
      <td>${Number(row.quantity).toLocaleString("vi-VN")}</td>
      <td>${money(row.unit_price)}</td>
    </tr>
  `).join("") || emptyRow(6, "Không có giao dịch phù hợp");
}

$("#history-filter")?.addEventListener("submit", async event => {
  event.preventDefault();

  const from = $("#history-from").value;
  const to = $("#history-to").value;

  if (from && to && from > to) {
    alert("Ngày bắt đầu không được lớn hơn ngày kết thúc.");
    return;
  }

  try {
    await loadHistory();
  } catch (error) {
    console.error(error);
    alert("Không tải được lịch sử giao dịch. Vui lòng thử lại.");
  }
});

$("#history-reset")?.addEventListener("click", async () => {
  $("#history-filter").reset();

  try {
    await loadHistory();
  } catch (error) {
    console.error(error);
    alert("Không tải được lịch sử giao dịch. Vui lòng thử lại.");
  }
});

const titles = {
  dashboard: "Tổng quan",
  products: "Quản lý sản phẩm",
  imports: "Nhập kho",
  exports: "Xuất kho",
  history: "Lịch sử giao dịch"
};

async function navigate(page) {
  document.querySelectorAll(".page").forEach(section => {
    section.classList.toggle("hidden", section.id !== `${page}-page`);
  });
  document.querySelectorAll(".nav[data-page]").forEach(button => {
    button.classList.toggle("active", button.dataset.page === page);
  });
  $("#page-title").textContent = titles[page] || "Tổng quan";

  try {
    if (page === "dashboard") await loadDashboard();
    if (page === "products") await loadProducts($("#search").value.trim());
    if (page === "imports" || page === "exports") {
      await loadProducts();
      if (page === "imports") await loadSuppliers();
    }
    if (page === "history") await loadHistory();
  } catch (error) {
    showMessage(error.message, true);
  }
}

function openProductDialog(product = null) {
  const form = $("#product-form");
  form.reset();
  form.elements.id.value = product?.id || "";
  $("#dialog-title").textContent = product ? "Chỉnh sửa sản phẩm" : "Thêm sản phẩm";
  if (product) {
    for (const key of [
      "code", "name", "category_id", "unit", "quantity",
      "import_price", "sale_price", "min_stock"
    ]) {
      form.elements[key].value = product[key] ?? "";
    }
  } else {
    form.elements.quantity.value = 0;
    form.elements.import_price.value = 0;
    form.elements.sale_price.value = 0;
    form.elements.min_stock.value = 0;
  }
  $("#product-dialog").showModal();
}

function formObject(form) {
  return Object.fromEntries(new FormData(form).entries());
}

$("#product-form").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = formObject(form);
  const id = data.id;
  delete data.id;
for (const key of ["import_price", "sale_price"]) {
  const raw = String(data[key] ?? "").trim();

  if (!/^\d[\d.,]*$/.test(raw)) {
    showMessage("Vui lòng nhập giá tiền hợp lệ", true);
    return;
  }

  data[key] = Number(raw.replace(/[.,]/g, ""));

  if (!Number.isFinite(data[key]) || data[key] < 0) {
    showMessage("Giá tiền không hợp lệ", true);
    return;
  }
}

  try {
    await api(id ? `/api/products/${id}` : "/api/products", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(data)
    });
    $("#product-dialog").close();
    showMessage(id ? "Đã cập nhật sản phẩm" : "Đã thêm sản phẩm");
    await loadProducts($("#search").value.trim());
    await loadDashboard();
  } catch (error) {
    showMessage(error.message, true);
  }
});

$("#products-table").addEventListener("click", async event => {
  const editId = event.target.dataset.edit;
  const deleteId = event.target.dataset.delete;

  if (editId) {
    const product = productsCache.find(p => p.id === Number(editId));
    if (product) openProductDialog(product);
  }

  if (deleteId && confirm("Bạn có chắc muốn xóa sản phẩm này?")) {
    try {
      await api(`/api/products/${deleteId}`, { method: "DELETE" });
      showMessage("Đã xóa sản phẩm");
      await loadProducts($("#search").value.trim());
      await loadDashboard();
    } catch (error) {
      showMessage(error.message, true);
    }
  }
});

$("#add-product").addEventListener("click", async () => {
  try {
    await loadCategories();
    openProductDialog();
  } catch (error) {
    showMessage(error.message, true);
  }
});

$("#close-dialog").addEventListener("click", () => $("#product-dialog").close());
$("#cancel-dialog").addEventListener("click", () => $("#product-dialog").close());
$("#search-button").addEventListener("click", () => loadProducts($("#search").value.trim()));
$("#search").addEventListener("keydown", event => {
  if (event.key === "Enter") loadProducts(event.currentTarget.value.trim());
});

document.querySelectorAll(".nav[data-page]").forEach(button => {
  button.addEventListener("click", () => navigate(button.dataset.page));
});
document.querySelectorAll("[data-goto]").forEach(button => {
  button.addEventListener("click", () => navigate(button.dataset.goto));
});

async function submitReceipt(event, kind) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = formObject(form);
  const productId = Number(data.product_id);
  const product = productsCache.find(p => p.id === productId);

  if (!product) {
    showMessage("Vui lòng chọn sản phẩm hợp lệ", true);
    return;
  }

  const payload = {
    code: data.code.trim(),
    user_id: 1,
    note: data.note || "",
    details: [{
      product_id: productId,
      quantity: Number(data.quantity),
      unit_price: Number(data.unit_price)
    }]
  };

  if (kind === "import") {
    payload.supplier_id = Number(data.supplier_id);
  } else {
    payload.receiver = data.receiver || "";
  }

  try {
    await api(`/api/${kind === "import" ? "imports" : "exports"}`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    form.reset();
    form.elements.quantity.value = 1;
    form.elements.unit_price.value = 0;
    showMessage(kind === "import" ? "Nhập kho thành công" : "Xuất kho thành công");
    await loadProducts();
    await loadDashboard();
  } catch (error) {
    showMessage(error.message, true);
  }
}

$("#import-form").addEventListener("submit", event => submitReceipt(event, "import"));
$("#export-form").addEventListener("submit", event => submitReceipt(event, "export"));

async function init() {
  try {
    await api("/api/health");
    await loadCategories();
    await loadDashboard();
  } catch (error) {
    showMessage(`Không thể khởi tạo ứng dụng: ${error.message}`, true);
  }
}

init();
const logoutButton = document.getElementById("logout-button");

if (logoutButton) {
    logoutButton.addEventListener("click", async () => {
        try {
            const response = await fetch("/api/logout", {
                method: "POST"
            });

            if (!response.ok) {
                throw new Error("Không thể đăng xuất");
            }

            window.location.href = "/";
        } catch (error) {
            alert(error.message);
        }
    });
}
