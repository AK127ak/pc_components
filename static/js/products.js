(function () {
    const tbody = document.getElementById("products-body");
    const emptyMsg = document.getElementById("empty-msg");
    const initialData = JSON.parse(document.getElementById("initial-products").textContent);

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str == null ? "" : str;
        return div.innerHTML;
    }

    function formatPrice(value) {
        return Number(value).toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function rowClass(product) {
        if (product.quantity === 0) return "row-out-of-stock";
        if (product.discount > 15) return "row-big-discount";
        return "";
    }

    function priceCell(product) {
        if (product.discount && product.discount > 0) {
            return (
                '<span class="price-old">' + formatPrice(product.price) + ' ₽</span> ' +
                '<span class="price-new">' + formatPrice(product.final_price) + ' ₽</span>'
            );
        }
        return '<span class="price-normal">' + formatPrice(product.price) + ' ₽</span>';
    }

    function renderRows(products) {
        tbody.innerHTML = "";
        if (!products.length) {
            emptyMsg.style.display = "block";
            return;
        }
        emptyMsg.style.display = "none";

        products.forEach(function (p) {
            const tr = document.createElement("tr");
            tr.className = rowClass(p);
            if (window.CAN_MANAGE) {
                tr.classList.add("row-clickable");
                tr.addEventListener("click", function () {
                    window.location.href = "/products/" + p.id + "/edit";
                });
            }
            tr.innerHTML =
                '<td><img class="thumb" src="/static/' + p.image_path + '" alt=""></td>' +
                '<td>' + escapeHtml(p.name) + '</td>' +
                '<td>' + escapeHtml(p.category) + '</td>' +
                '<td class="desc-cell">' + escapeHtml(p.description) + '</td>' +
                '<td>' + escapeHtml(p.manufacturer) + '</td>' +
                '<td>' + escapeHtml(p.supplier) + '</td>' +
                '<td>' + priceCell(p) + '</td>' +
                '<td>' + escapeHtml(p.unit) + '</td>' +
                '<td>' + p.quantity + '</td>' +
                '<td>' + (p.discount > 0 ? p.discount + '%' : '\u2014') + '</td>';
            tbody.appendChild(tr);
        });
    }

    // Первичный рендер (для всех ролей — гость/клиент видят полный список без фильтров)
    renderRows(initialData);

    if (!window.CAN_FILTER) {
        return; // гость/клиент — без поиска, сортировки, фильтрации
    }

    const searchInput = document.getElementById("search-input");
    const supplierSelect = document.getElementById("supplier-select");
    const sortBtn = document.getElementById("sort-btn");
    let currentSort = ""; // '', 'asc', 'desc'
    let debounceTimer = null;

    function sortLabel() {
        if (currentSort === "asc") return "Кол-во на складе: по возрастанию \u2191";
        if (currentSort === "desc") return "Кол-во на складе: по убыванию \u2193";
        return "Кол-во на складе: без сортировки";
    }

    function fetchProducts() {
        const params = new URLSearchParams();
        if (searchInput.value.trim()) params.set("q", searchInput.value.trim());
        if (supplierSelect.value) params.set("supplier", supplierSelect.value);
        if (currentSort) params.set("sort", currentSort);

        fetch("/api/products?" + params.toString())
            .then(function (resp) { return resp.json(); })
            .then(function (data) { renderRows(data); });
    }

    searchInput.addEventListener("input", function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(fetchProducts, 150);
    });

    supplierSelect.addEventListener("change", fetchProducts);

    sortBtn.addEventListener("click", function () {
        // Циклически: без сортировки -> возрастание -> убывание -> без сортировки
        currentSort = currentSort === "" ? "asc" : currentSort === "asc" ? "desc" : "";
        sortBtn.textContent = sortLabel();
        fetchProducts();
    });
})();
