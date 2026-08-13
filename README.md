# 🍽️ RezeptRoulette

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow?logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open%20App-success?style=for-the-badge&logo=render)](https://rezeptroulette-1.onrender.com/)

### Your solution to the everyday question: "What should I eat today?"

RezeptRoulette is a web application designed to make meal planning easier and help users discover new recipes.

It provides features for finding meal inspiration, planning meals, organizing recipes, and creating shopping lists.

## 🖼️ Preview

![RezeptRoulette Home Page](docs/screenshots/home.png)

## ✨ Features

- 🎲 **Recipe Roulette** – Get a random recipe suggestion when you don't know what to cook
- 🔍 **Recipe Discovery** – Browse and discover available recipes
- 📅 **Weekly Meal Planner** – Plan breakfast, lunch, and dinner for the entire week
- 🛒 **Smart Shopping List** – Automatically generate a shopping list from your meal plan
- ♻️ **Food Rescue** – Find recipes based on ingredients you already have
- ❤️ **Favorites** – Save your favorite recipes for quick access
- ⭐ **Recipe Ratings** – Rate recipes and keep track of your favorites
- 🌙 **Dark Mode** – Switch between light and dark themes

## 🛠️ Tech Stack

| Area | Technology |
|---|---|
| **Backend** | Python, FastAPI |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Database** | SQLite |
| **API** | REST API |
| **Deployment** | Render |
| **Version Control** | Git & GitHub |

## 📸 Application Preview

### 🔍 Recipe Discovery

Search and filter recipes by category, preparation time, difficulty, favorites, and more.

<img src="docs/screenshots/recipes.png" width="800" alt="Recipe Discovery">

### 🎲 Recipe Roulette

Can't decide what to cook? Recipe Roulette randomly selects a recipe based on your preferences.

<img src="docs/screenshots/roulette.png" width="800" alt="Recipe Roulette">

### 📅 Meal Planning & Shopping

Plan breakfast, lunch, and dinner for the entire week. The shopping list is automatically generated from your planned meals.

<p>
  <img src="docs/screenshots/planner.png" width="49%" alt="Weekly Meal Planner">
  <img src="docs/screenshots/shopping-list.png" width="49%" alt="Shopping List">
</p>

### ♻️ Food Rescue

Enter ingredients you already have at home and discover recipes that match your available ingredients.

<img src="docs/screenshots/food-rescue.png" width="800" alt="Food Rescue">

## 🚀 Live Demo

RezeptRoulette is deployed and available online.

👉 **[Try RezeptRoulette Live](https://rezeptroulette-1.onrender.com/)**

> **Note:** The application is hosted on Render. The first request may take a few seconds if the service is currently inactive.

## 📂 Project Structure

```text
Rezeptroulette/
├── bilder/              # Recipe images
├── data/                # Application data
├── docs/
│   └── screenshots/     # README screenshots
├── services/            # Application services
├── static/              # Frontend assets
├── api.py               # API endpoints
├── app.py               # Application setup
├── config.py            # Configuration
├── database.py          # Database access
├── main.py              # Application entry point
├── models.py            # Data models
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## ⚙️ Local Installation

Clone the repository:

```bash
git clone https://github.com/Pexiz96/Rezeptroulette.git
```

Navigate into the project directory:

```bash
cd Rezeptroulette
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment on Windows:

```bash
.venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 👨‍💻 Author

Developed by **Pexiz96**

This project was created as part of my journey in software development and is continuously being improved.
