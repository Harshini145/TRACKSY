CREATE DATABASE tracksy;
USE tracksy;

-- ================= USERS (LOGIN SYSTEM) =================
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================= CATEGORIES =================
CREATE TABLE Categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- ================= EXPENSES =================
CREATE TABLE Expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    category_id INT,
    description TEXT,
    amount DECIMAL(10,2),
    expense_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id)
);

-- ================= MONTHLY BUDGET =================
CREATE TABLE Monthly_Budgets (
    budget_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    month INT,
    year INT,
    amount DECIMAL(10,2),

    UNIQUE(user_id, month, year),

    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- ================= CATEGORY BUDGET =================
CREATE TABLE Category_Budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    category_id INT,
    month INT,
    year INT,
    amount DECIMAL(10,2),

    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id)
);

-- ================= USER SETTINGS =================
CREATE TABLE User_Settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    theme VARCHAR(20),

    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- ================= NOTIFICATIONS =================
CREATE TABLE Notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    message TEXT,
    type ENUM('warning','alert'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);