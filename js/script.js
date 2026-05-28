// ============================================================
// Tracksy Frontend — wired to FastAPI backend at localhost:8000
// ============================================================
const API = (() => {
    if (window.TRACKSY_API_URL) return window.TRACKSY_API_URL.replace(/\/$/, "");
    if (window.location.protocol === "file:") return "http://127.0.0.1:8000";
    if (["8000", ""].includes(window.location.port)) return window.location.origin;
    return `${window.location.protocol}//${window.location.hostname}:8000`;
})();

// ── Auth state ──────────────────────────────────────────────
let authToken   = localStorage.getItem("tracksy_token") || null;
let currentUser = JSON.parse(localStorage.getItem("tracksy_user") || "null");
const resetToken = new URLSearchParams(window.location.search).get("reset_token");

// ── Helpers ─────────────────────────────────────────────────
function authHeaders() {
    return { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` };
}

async function apiFetch(path, options = {}) {
    const res = await fetch(API + path, options);
    if (res.status === 401) { logout(); return null; }
    return res;
}

function showToast(msg, type = "success") {
    let t = document.getElementById("toast");
    if (!t) {
        t = document.createElement("div");
        t.id = "toast";
        t.style.cssText = "position:fixed;bottom:30px;left:50%;transform:translateX(-50%);padding:14px 28px;border-radius:12px;font-weight:600;font-size:0.95rem;z-index:9999;transition:all 0.3s;opacity:0;font-family:'Inter',sans-serif;";
        document.body.appendChild(t);
    }
    t.textContent = msg;
    t.style.background = type === "success" ? "var(--primary)" : "var(--danger)";
    t.style.color = "#fff";
    t.style.opacity = "1";
    setTimeout(() => { t.style.opacity = "0"; }, 3000);
}

// ── Init ─────────────────────────────────────────────────────
window.onload = () => {
    if (resetToken) {
        localStorage.removeItem("tracksy_token");
        localStorage.removeItem("tracksy_user");
        document.getElementById("authPage").style.display = "flex";
        document.getElementById("app").style.display      = "none";
        showResetPasswordMode();
    } else if (authToken && currentUser) {
        document.getElementById("authPage").style.display = "none";
        document.getElementById("app").style.display      = "flex";
        initApp();
    } else {
        document.getElementById("authPage").style.display = "flex";
        document.getElementById("app").style.display      = "none";
    }
};

function showResetPasswordMode() {
    document.getElementById("usernameGroup").style.display = "none";
    document.getElementById("emailGroup").style.display = "none";
    document.getElementById("password").value = "";
    document.getElementById("password").placeholder = "New password";
    document.getElementById("resetNotice").style.display = "block";
    document.querySelector(".auth-buttons .btn-primary").style.display = "none";
    document.querySelector(".auth-buttons .btn-secondary").style.display = "none";
    document.querySelector(".auth-buttons .btn-link").style.display = "none";
    document.getElementById("resetPasswordBtn").style.display = "flex";
}

// ── Auth: Login ──────────────────────────────────────────────
window.login = async function () {
    const email    = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    if (!email || !password) { showToast("Please fill all fields", "error"); return; }

    try {
        const res  = await fetch(`${API}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: email, password })
        });
        const data = await res.json();
        if (!res.ok) { showToast(data.detail || "Login failed", "error"); return; }

        authToken   = data.access_token;
        currentUser = { user_id: data.user_id, username: data.username, email: data.email };
        localStorage.setItem("tracksy_token", authToken);
        localStorage.setItem("tracksy_user",  JSON.stringify(currentUser));

        showToast(`Welcome back, ${data.username}!`);
        setTimeout(() => location.reload(), 800);
    } catch (e) {
        showToast("Could not reach backend. Make sure the server is running.", "error");
    }
};

// ── Auth: Signup ─────────────────────────────────────────────
window.signup = async function () {
    const username = document.getElementById("username").value.trim();
    const email    = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    if (!username || !email || !password) { showToast("Please fill all fields", "error"); return; }

    try {
        const res  = await fetch(`${API}/auth/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password })
        });
        const data = await res.json();
        if (!res.ok) { showToast(data.detail || "Signup failed", "error"); return; }

        authToken   = data.access_token;
        currentUser = { user_id: data.user_id, username: data.username, email: data.email };
        localStorage.setItem("tracksy_token", authToken);
        localStorage.setItem("tracksy_user",  JSON.stringify(currentUser));

        showToast(`Account created! Welcome, ${data.username}!`);
        setTimeout(() => location.reload(), 800);
    } catch (e) {
        showToast("Could not reach backend. Make sure the server is running.", "error");
    }
};

window.forgotPassword = async function () {
    const email = document.getElementById("email").value.trim();
    if (!email) { showToast("Enter your email first", "error"); return; }

    try {
        const res = await fetch(`${API}/auth/forgot-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });
        const data = await res.json();
        if (!res.ok) { showToast(data.detail || "Could not send reset email", "error"); return; }
        showToast(data.message || "Password reset email sent!");
    } catch (e) {
        showToast("Could not reach backend. Make sure the server is running.", "error");
    }
};

window.resetPassword = async function () {
    const password = document.getElementById("password").value;
    if (!password || password.length < 6) {
        showToast("Password must be at least 6 characters", "error");
        return;
    }

    try {
        const res = await fetch(`${API}/auth/reset-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: resetToken, password })
        });
        const data = await res.json();
        if (!res.ok) { showToast(data.detail || "Could not reset password", "error"); return; }
        showToast(data.message || "Password reset successful");
        setTimeout(() => {
            window.location.href = `${window.location.origin}${window.location.pathname}`;
        }, 1000);
    } catch (e) {
        showToast("Could not reach backend. Make sure the server is running.", "error");
    }
};

// ── Auth: Logout ─────────────────────────────────────────────
window.logout = function () {
    localStorage.removeItem("tracksy_token");
    localStorage.removeItem("tracksy_user");
    authToken   = null;
    currentUser = null;
    location.reload();
};

// ============================================================
// MAIN APP — runs after login
// ============================================================
function initApp() {

// ── State ───────────────────────────────────────────────────
let categories = [];
let expenses   = [];
let budgets    = {};   // key: "month-year" → { budget_id, amount }
let chart;

const DEFAULT_CATEGORIES = ["Food", "Transport", "Shopping", "Health", "Rent", "Utilities", "Education", "Entertainment"];

function userStoragePrefix() {
    return `tracksy_${currentUser?.user_id || "guest"}`;
}

function categoryStorageKey() {
    return `${userStoragePrefix()}_categories`;
}

function expenseStorageKey() {
    return `${userStoragePrefix()}_expenses`;
}

function defaultCategories() {
    return DEFAULT_CATEGORIES.map((name, index) => ({
        category_id: -(index + 1),
        name
    }));
}

function loadLocalCategories() {
    const raw = localStorage.getItem(categoryStorageKey());
    if (!raw) return defaultCategories();
    try {
        const saved = JSON.parse(raw);
        return Array.isArray(saved) && saved.length ? saved : defaultCategories();
    } catch (e) {
        return defaultCategories();
    }
}

function saveLocalCategories(nextCategories) {
    localStorage.setItem(categoryStorageKey(), JSON.stringify(nextCategories));
}

function addLocalCategory(name) {
    const existing = loadLocalCategories();
    const match = existing.find(c => c.name.toLowerCase() === name.toLowerCase());
    if (match) return match;
    const minId = existing.reduce((min, c) => Math.min(min, Number(c.category_id) || 0), 0);
    const category = { category_id: minId - 1, name };
    const updated = [...existing, category];
    saveLocalCategories(updated);
    return category;
}

function loadLocalExpenses() {
    const raw = localStorage.getItem(expenseStorageKey());
    if (!raw) return [];
    try {
        const saved = JSON.parse(raw);
        return Array.isArray(saved) ? saved : [];
    } catch (e) {
        return [];
    }
}

function saveLocalExpense(expense) {
    const saved = loadLocalExpenses();
    const nextExpense = {
        ...expense,
        expense_id: Date.now(),
        category_name: categories.find(c => Number(c.category_id) === Number(expense.category_id))?.name || "Uncategorized",
    };
    const updated = [...saved, nextExpense];
    localStorage.setItem(expenseStorageKey(), JSON.stringify(updated));
    return nextExpense;
}

function budgetStorageKey(month, year) {
    return `${userStoragePrefix()}_budget_${month}_${year}`;
}

function saveLocalBudget(month, year, amount) {
    const key = `${month}-${year}`;
    budgets[key] = { amount };
    localStorage.setItem(budgetStorageKey(month, year), String(amount));
}

function loadLocalBudget(month, year) {
    const raw = localStorage.getItem(budgetStorageKey(month, year));
    if (raw == null) return null;
    const amount = parseFloat(raw);
    return Number.isFinite(amount) ? amount : null;
}

// ── DOM refs ─────────────────────────────────────────────────
const mSel          = document.getElementById("monthSelect");
const ySel          = document.getElementById("yearSelect");
const categorySelect= document.getElementById("category");
const listEl        = document.getElementById("expenseList");
const totalEl       = document.getElementById("total");
const budgetEl      = document.getElementById("budget");
const remainingEl   = document.getElementById("remaining");

// Greet user
document.querySelector("#homePage .header h1").textContent =
    `Welcome back, ${currentUser.username} 👋`;

// ── Month / Year selectors ───────────────────────────────────
const months = ["January","February","March","April","May","June",
                "July","August","September","October","November","December"];
months.forEach((m, i) => {
    const o = document.createElement("option");
    o.value = i; o.text = m;
    mSel.appendChild(o);
});
for (let y = 2023; y <= 2030; y++) {
    const o = document.createElement("option");
    o.value = y; o.text = y;
    ySel.appendChild(o);
}
const now = new Date();
mSel.value = now.getMonth();
ySel.value = now.getFullYear();

mSel.addEventListener("change", renderAll);
ySel.addEventListener("change", renderAll);

// ── Navigation ───────────────────────────────────────────────
window.showPage = function (p) {
    ["home","dashboard","add","list","food"].forEach(x => {
        const pg = document.getElementById(x + "Page");
        if (pg) pg.style.display = "none";
        const nav = document.getElementById("nav-" + x);
        if (nav) nav.classList.remove("active");
    });
    const page = document.getElementById(p + "Page");
    if (page) page.style.display = "block";
    const nav = document.getElementById("nav-" + p);
    if (nav) nav.classList.add("active");

    // Retrigger fade-up animations
    if (page) {
        page.querySelectorAll(".fade-up").forEach(el => {
            el.style.animation = "none";
            el.offsetHeight;
            el.style.animation = null;
        });
    }
    renderAll();
};

// ── Load all data ─────────────────────────────────────────────
async function loadAll() {
    await Promise.all([loadCategories(), loadExpenses(), loadBudget()]);
    renderAll();
}

// ── Categories ───────────────────────────────────────────────
async function loadCategories() {
    try {
        const res  = await apiFetch("/categories/", { headers: authHeaders() });
        if (!res) {
            categories = loadLocalCategories();
            populateCategorySelect();
            return;
        }
        const data = await res.json();
        categories = Array.isArray(data) && data.length ? data : loadLocalCategories();
        if (Array.isArray(data) && data.length) saveLocalCategories(data);
        populateCategorySelect();
    } catch (e) {
        categories = loadLocalCategories();
        populateCategorySelect();
        console.error("loadCategories:", e);
    }
}

function populateCategorySelect() {
    categorySelect.innerHTML = "";
    if (!categories.length) categories = loadLocalCategories();
    categories.forEach(c => {
        const o = document.createElement("option");
        o.value = c.category_id;
        o.text  = c.name;
        categorySelect.appendChild(o);
    });
    const add = document.createElement("option");
    add.value = "add_new";
    add.text  = "➕ Add New Category";
    categorySelect.appendChild(add);
}

// ── Category popup ────────────────────────────────────────────
let selectedCategory = "";

categorySelect.addEventListener("change", function () {
    if (this.value === "add_new") {
        document.getElementById("popup").style.display = "flex";
        loadPopup();
    }
});

function loadPopup() {
    const list = document.getElementById("catList");
    list.innerHTML = "";
    const arr = ["Health","Education","Gym","Rent","Groceries","Utilities","Food","Travel","Shopping","Others"];
    arr.forEach(c => {
        const b = document.createElement("button");
        b.innerText = c;
        if (c === selectedCategory) b.classList.add("selected");
        b.onclick = () => {
            selectedCategory = c;
            Array.from(list.children).forEach(btn => btn.classList.remove("selected"));
            b.classList.add("selected");
            document.getElementById("customCat").style.display =
                c === "Others" ? "block" : "none";
        };
        list.appendChild(b);
    });
}

window.confirmCategory = async function () {
    const val = selectedCategory === "Others"
        ? document.getElementById("customCat").value.trim()
        : selectedCategory;
    if (!val) { closePopup(); return; }

    try {
        const res = await apiFetch("/categories/", {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ name: val })
        });
        if (res && res.ok) {
            await loadCategories();
            const match = categories.find(c => c.name === val);
            if (match) categorySelect.value = match.category_id;
            showToast(`Category "${val}" added!`);
        } else {
            const category = addLocalCategory(val);
            categories = loadLocalCategories();
            populateCategorySelect();
            categorySelect.value = category.category_id;
            showToast(`Category "${val}" added locally!`);
        }
    } catch (e) {
        const category = addLocalCategory(val);
        categories = loadLocalCategories();
        populateCategorySelect();
        categorySelect.value = category.category_id;
        showToast(`Category "${val}" added locally!`);
        console.error(e);
    }
    closePopup();
};

window.closePopup = function () {
    document.getElementById("popup").style.display = "none";
    document.getElementById("customCat").value = "";
    selectedCategory = "";
    if (categorySelect.value === "add_new" && categories.length > 0) {
        categorySelect.value = categories[0].category_id;
    }
};

// ── Expenses: Load ────────────────────────────────────────────
async function loadExpenses() {
    try {
        const month = parseInt(mSel.value) + 1;
        const year  = parseInt(ySel.value);
        const res   = await apiFetch(`/expenses/?month=${month}&year=${year}`, { headers: authHeaders() });
        if (!res) {
            expenses = loadLocalExpenses().filter(e => {
                const date = new Date(e.expense_date);
                return date.getMonth() + 1 === month && date.getFullYear() === year;
            });
            return;
        }
        const data = await res.json();
        const local = loadLocalExpenses().filter(e => {
            const date = new Date(e.expense_date);
            return date.getMonth() + 1 === month && date.getFullYear() === year;
        });
        expenses = Array.isArray(data) ? [...data, ...local] : local;
    } catch (e) {
        const month = parseInt(mSel.value) + 1;
        const year  = parseInt(ySel.value);
        expenses = loadLocalExpenses().filter(expense => {
            const date = new Date(expense.expense_date);
            return date.getMonth() + 1 === month && date.getFullYear() === year;
        });
        console.error("loadExpenses:", e);
    }
}

// ── Expenses: Add ─────────────────────────────────────────────
document.getElementById("expenseForm").addEventListener("submit", async e => {
    e.preventDefault();
    const desc       = document.getElementById("desc").value.trim();
    const amount     = parseFloat(document.getElementById("amount").value);
    const cat_id     = parseInt(categorySelect.value);
    const today      = new Date().toISOString().split("T")[0];

    if (!desc || !amount || isNaN(cat_id)) {
        showToast("Please fill all fields", "error");
        return;
    }

    try {
        const res = await apiFetch("/expenses/", {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({
                description:  desc,
                amount:       amount,
                category_id:  cat_id,
                expense_date: today
            })
        });
        if (res && res.ok) {
            showToast("Expense added!");
            e.target.reset();
            await loadAll();
            showPage("list");
        } else {
            if (res && res.status >= 400) {
                saveLocalExpense({
                    description: desc,
                    amount,
                    category_id: cat_id,
                    expense_date: today
                });
                showToast("Expense saved locally!");
                e.target.reset();
                await loadAll();
                showPage("list");
                return;
            }
            const err = res ? await res.json() : {};
            showToast(err.detail || "Failed to add expense", "error");
        }
    } catch (err) {
        saveLocalExpense({
            description: desc,
            amount,
            category_id: cat_id,
            expense_date: today
        });
        showToast("Expense saved locally!");
        e.target.reset();
        await loadAll();
        showPage("list");
    }
});

// ── Expenses: Delete ──────────────────────────────────────────
window.deleteExpense = async function (id) {
    if (!confirm("Delete this expense?")) return;
    try {
        await apiFetch(`/expenses/${id}`, { method: "DELETE", headers: authHeaders() });
        showToast("Expense deleted");
        await loadAll();
    } catch (e) { console.error(e); }
};

// ── Budget: Load ──────────────────────────────────────────────
async function loadBudget() {
    const month = parseInt(mSel.value) + 1;
    const year  = parseInt(ySel.value);
    const key   = `${month}-${year}`;

    try {
        const res   = await apiFetch(`/budgets/monthly?month=${month}&year=${year}`, { headers: authHeaders() });
        if (!res) return;
        const data  = await res.json();
        if (data && data.budget != null) {
            budgets[key] = { amount: parseFloat(data.budget) };
        } else {
            const localAmount = loadLocalBudget(month, year);
            if (localAmount != null) budgets[key] = { amount: localAmount };
            else delete budgets[key];
        }
    } catch (e) {
        const localAmount = loadLocalBudget(month, year);
        if (localAmount != null) budgets[key] = { amount: localAmount };
        console.error("loadBudget:", e);
    }
}

// ── Budget: Set ───────────────────────────────────────────────
window.setBudget = async function () {
    const amount = parseFloat(document.getElementById("budgetInput").value);
    if (!amount || isNaN(amount)) { showToast("Enter a valid amount", "error"); return; }

    const month = parseInt(mSel.value) + 1;
    const year  = parseInt(ySel.value);
    try {
        const res = await apiFetch("/budgets/monthly", {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ month, year, amount })
        });

        if (res && res.ok) {
            saveLocalBudget(month, year, amount);
            showToast(`Budget set to ₹${amount.toLocaleString()}!`);
            document.getElementById("budgetInput").value = "";
            await loadBudget();
            renderAll();
            showPage("dashboard");
        } else {
            if (res && res.status >= 500) {
                saveLocalBudget(month, year, amount);
                showToast(`Budget saved locally: Rs.${amount.toLocaleString()}!`);
                document.getElementById("budgetInput").value = "";
                renderAll();
                showPage("dashboard");
                return;
            }
            const err = res ? await res.json() : {};
            showToast(err.detail || "Failed to set budget", "error");
        }
    } catch (e) {
        saveLocalBudget(month, year, amount);
        showToast(`Budget saved locally: Rs.${amount.toLocaleString()}!`);
        document.getElementById("budgetInput").value = "";
        renderAll();
        showPage("dashboard");
    }
};

// ── Render helpers ────────────────────────────────────────────
function renderAll() {
    loadExpenses().then(() => {
        render();
        loadList();
    });
    loadBudget().then(() => render());
}

const catIcons = {
    "Food":"fa-utensils","Travel":"fa-plane","Shopping":"fa-shopping-bag",
    "Health":"fa-heartbeat","Education":"fa-graduation-cap","Gym":"fa-dumbbell",
    "Rent":"fa-home","Groceries":"fa-shopping-cart","Utilities":"fa-bolt",
    "Others":"fa-tag"
};
function getIconForCat(name) { return catIcons[name] || "fa-receipt"; }

// ── Expense List ──────────────────────────────────────────────
function loadList() {
    listEl.innerHTML = "";
    if (!expenses || expenses.length === 0) {
        listEl.innerHTML = `<li class="text-muted" style="justify-content:center;padding:30px;">No expenses found for this month.</li>`;
        return;
    }
    [...expenses].reverse().forEach(e => {
        const li = document.createElement("li");
        li.innerHTML = `
            <div class="expense-info">
                <div class="expense-icon">
                    <i class="fas ${getIconForCat(e.category_name || "")}"></i>
                </div>
                <div class="expense-details">
                    <h4>${e.description || "—"}</h4>
                    <span class="text-muted small">${e.category_name || "Uncategorized"} • ${e.expense_date}</span>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:15px;">
                <span class="expense-amount">₹${parseFloat(e.amount).toLocaleString()}</span>
                <button class="delete-btn" onclick="deleteExpense(${e.expense_id})"><i class="fas fa-trash"></i></button>
            </div>
        `;
        listEl.appendChild(li);
    });
}

// ── Dashboard Chart ───────────────────────────────────────────
function render() {
    const month = parseInt(mSel.value) + 1;
    const year  = parseInt(ySel.value);
    const key   = `${month}-${year}`;

    const total  = expenses.reduce((s, e) => s + parseFloat(e.amount), 0);
    const budget = budgets[key] ? budgets[key].amount : 0;
    const rem    = budget - total;

    totalEl.innerText     = "₹" + total.toLocaleString();
    budgetEl.innerText    = "₹" + budget.toLocaleString();
    remainingEl.innerText = "₹" + rem.toLocaleString();
    remainingEl.style.color = rem < 0 ? "var(--danger)" : "var(--success)";

    // Build chart data from expenses by category
    const data = {};
    expenses.forEach(e => {
        const cat = e.category_name || "Other";
        data[cat] = (data[cat] || 0) + parseFloat(e.amount);
    });

    if (chart) chart.destroy();

    const colors = ['#10B981','#0D9488','#3B82F6','#F59E0B','#6366F1','#8B5CF6','#EC4899','#64748B'];

    chart = new Chart(document.getElementById("chart"), {
        type: "doughnut",
        data: {
            labels: Object.keys(data),
            datasets: [{
                data:            Object.values(data),
                backgroundColor: colors,
                borderWidth:     0,
                hoverOffset:     4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "75%",
            plugins: {
                legend: {
                    position: "right",
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        color: "#94A3B8",
                        font: { family: "'Inter', sans-serif", size: 13 }
                    }
                },
                tooltip: {
                    backgroundColor: "#151D2C",
                    borderColor: "rgba(255,255,255,0.05)",
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: { family: "'Inter', sans-serif" },
                    bodyFont:  { family: "'Inter', sans-serif" }
                }
            }
        }
    });
}

// ── Restaurants / Food Spots ──────────────────────────────────
window.findFoodSpots = function () {
    const loader     = document.getElementById("foodLoader");
    const loaderText = document.getElementById("foodLoaderText");
    const results    = document.getElementById("foodResults");

    loader.style.display  = "block";
    results.innerHTML     = "";
    loaderText.innerText  = "Accessing live location...";

    if (!navigator.geolocation) {
        loader.style.display = "none";
        results.innerHTML = '<p class="text-muted text-center w-100">Geolocation is not supported by your browser.</p>';
        return;
    }

    navigator.geolocation.getCurrentPosition(async (pos) => {
        loaderText.innerText = "Finding affordable spots nearby...";
        const { latitude, longitude } = pos.coords;
        try {
            const res = await fetch(`${API}/food-spots/nearby?lat=${latitude}&lon=${longitude}&radius=1500&limit=1`);
            if (!res.ok) throw new Error("Backend error");
            const data = await res.json();
            loader.style.display = "none";

            if (data.spots && data.spots.length > 0) {
                data.spots.slice(0, 1).forEach(spot => {
                    const card = document.createElement("div");
                    card.className = "card fade-up p-0";
                    card.style.overflow = "hidden";
                    card.style.cursor = "pointer";
                    card.setAttribute("role", "link");
                    card.setAttribute("tabindex", "0");
                    const cuisine = spot.cuisine || "Various";
                    const hours   = spot.opening_hours || "Hours vary";
                    const mapsLink = spot.maps_link || `https://www.google.com/maps/search/?api=1&query=${spot.lat},${spot.lon}`;
                    card.onclick = () => window.open(mapsLink, "_blank", "noopener");
                    card.onkeydown = (event) => {
                        if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            window.open(mapsLink, "_blank", "noopener");
                        }
                    };
                    card.innerHTML = `
                        <div style="padding:20px;">
                            <h3 style="margin-bottom:5px;font-size:1.15rem;">${spot.name}</h3>
                            <p class="text-muted small" style="margin-bottom:15px;">
                                <i class="fa-solid fa-utensils"></i> ${cuisine} &bull;
                                <i class="fa-regular fa-clock"></i> ${hours}
                            </p>
                            <span style="display:inline-block;padding:4px 10px;background:rgba(16,185,129,0.1);color:var(--primary);border-radius:8px;font-size:0.8rem;font-weight:600;margin-bottom:15px;">Budget Friendly</span>
                            <a href="${mapsLink}" target="_blank" rel="noopener" class="w-100"
                               style="display:block;text-align:center;padding:10px;background:rgba(255,255,255,0.05);color:var(--text-main);text-decoration:none;border-radius:8px;border:1px solid var(--surface-border);transition:var(--transition);"
                               onclick="event.stopPropagation()"
                               onmouseover="this.style.background='var(--primary)';this.style.color='white'"
                               onmouseout="this.style.background='rgba(255,255,255,0.05)';this.style.color='var(--text-main)'">
                                <i class="fa-solid fa-map-location-dot"></i> Open in Maps
                            </a>
                        </div>`;
                    results.appendChild(card);
                });
            } else {
                results.innerHTML = '<p class="text-muted text-center w-100" style="padding:30px;">No affordable spots found within 1.5km.</p>';
            }
        } catch (err) {
            loader.style.display = "none";
            results.innerHTML = `
                <div class="card w-100 text-center" style="border-color:var(--danger);">
                    <i class="fa-solid fa-triangle-exclamation fa-2x" style="color:var(--danger);margin-bottom:15px;"></i>
                    <p class="text-main">Failed to connect to backend.</p>
                    <p class="text-muted small mt-3">Make sure the server is running: <code>uvicorn main:app --reload</code></p>
                </div>`;
        }
    }, (err) => {
        loader.style.display = "none";
        results.innerHTML = '<p class="text-muted text-center w-100" style="padding:30px;">Failed to get location. Please allow location access.</p>';
    }, { enableHighAccuracy: true, timeout: 10000 });
};

// ── Bootstrap ─────────────────────────────────────────────────
loadAll();

} // end initApp
