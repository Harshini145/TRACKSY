// ===== STORAGE =====
let categories = JSON.parse(localStorage.getItem("categories")) || ["Food","Travel","Shopping"];
let expenses = JSON.parse(localStorage.getItem("expenses")) || [];
let budgets = JSON.parse(localStorage.getItem("budgets")) || {};
let chart;

// ===== ELEMENTS =====
const mSel = document.getElementById("monthSelect");
const ySel = document.getElementById("yearSelect");
const categorySelect = document.getElementById("category");

const totalEl = document.getElementById("total");
const budgetEl = document.getElementById("budget");
const remainingEl = document.getElementById("remaining");

// ===== MONTHS =====
const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

months.forEach((m,i)=>{
    let o=document.createElement("option");
    o.value=i;
    o.text=m;
    mSel.appendChild(o);
});

// ===== YEARS =====
for(let y=2023;y<=2030;y++){
    let o=document.createElement("option");
    o.value=y;
    o.text=y;
    ySel.appendChild(o);
}

// ===== DEFAULT =====
let d=new Date();
mSel.value=d.getMonth();
ySel.value=d.getFullYear();

// ===== LOAD CATEGORIES =====
function loadCategories(){
    categorySelect.innerHTML="";

    categories.forEach(c=>{
        let o=document.createElement("option");
        o.value=c;
        o.text=c;
        categorySelect.appendChild(o);
    });

    let add=document.createElement("option");
    add.value="add_new";
    add.text="➕ Add Category";
    categorySelect.appendChild(add);
}
loadCategories();

// ===== CATEGORY POPUP =====
let selectedCategory="";

categorySelect.addEventListener("change", function(){
    if(this.value==="add_new"){
        document.getElementById("popup").style.display="flex";
        loadPopup();
    }
});

function loadPopup(){
    let list=document.getElementById("catList");
    list.innerHTML="";

    let arr=["Health","Education","Gym","Rent","Groceries","Others"];

    arr.forEach(c=>{
        let b=document.createElement("button");
        b.innerText=c;

        b.onclick=()=>{
            selectedCategory=c;

            if(c==="Others"){
                document.getElementById("customCat").style.display="block";
            } else {
                document.getElementById("customCat").style.display="none";
            }
        };

        list.appendChild(b);
    });
}

function confirmCategory(){
    let custom = document.getElementById("customCat").value;

    let val = selectedCategory==="Others" ? custom : selectedCategory;

    if(val && !categories.includes(val)){
        categories.push(val);
        localStorage.setItem("categories", JSON.stringify(categories));
    }

    loadCategories();
    categorySelect.value = val;

    closePopup();
}

function closePopup(){
    document.getElementById("popup").style.display="none";
    document.getElementById("customCat").value="";
}

// ===== NAVIGATION =====
function showPage(p){
    ["home","dashboard","add","theme"].forEach(x=>{
        document.getElementById(x+"Page").style.display="none";
    });

    document.getElementById(p+"Page").style.display="block";

    if(p==="dashboard") render();
}

// ===== SET BUDGET =====
function setBudget(){
    let key = mSel.value+"-"+ySel.value;

    budgets[key] = parseInt(document.getElementById("budgetInput").value) || 0;

    localStorage.setItem("budgets", JSON.stringify(budgets));

    showPage("dashboard");
}

// ===== ADD EXPENSE =====
document.getElementById("expenseForm").addEventListener("submit", e=>{
    e.preventDefault();

    let today = new Date().toISOString().split("T")[0];

    let expense = {
        desc: document.getElementById("desc").value,
        amount: parseInt(document.getElementById("amount").value),
        category: categorySelect.value,
        date: today
    };

    expenses.push(expense);
    localStorage.setItem("expenses", JSON.stringify(expenses));

    e.target.reset();

    render(); // 🔥 LIVE UPDATE
});

// ===== DASHBOARD =====
function render(){
    let total = 0;
    let data = {};

    expenses.forEach(e=>{
        let d = new Date(e.date);

        if(d.getMonth()==mSel.value && d.getFullYear()==ySel.value){
            total += e.amount;
            data[e.category] = (data[e.category] || 0) + e.amount;
        }
    });

    let key = mSel.value+"-"+ySel.value;
    let budget = budgets[key] || 0;

    totalEl.innerText = "₹" + total;
    budgetEl.innerText = "₹" + budget;
    remainingEl.innerText = "₹" + (budget - total);

    if(chart) chart.destroy();

    chart = new Chart(document.getElementById("chart"), {
        type: "pie",
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data)
            }]
        }
    });
}

// ===== THEME =====
function setTheme(t){
    document.body.className = t;
    localStorage.setItem("theme", t);
}

// ===== LOAD =====
window.onload = ()=>{
    let t = localStorage.getItem("theme");
    if(t) document.body.className = t;

    render();
};