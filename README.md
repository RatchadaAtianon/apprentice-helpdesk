# 🛠️ Apprentice Helpdesk App

A simple Flask-based helpdesk ticketing system designed to help users submit, view, and manage support tickets. Built with Python, Flask, and Bootstrap.

🌐 **Live Demo**: [https://apprentice-helpdesk.onrender.com](https://apprentice-helpdesk.onrender.com)

---

## 📦 Features

- 📝 Submit and view support tickets
- 🎯 Filter tickets by priority and status
- 👩‍💼 Admin view to manage users
- 🔐 User authentication with roles (admin, apprentice)
- 💬 Flash messages for success/error feedback
- 📱 Responsive layout with mobile support

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/RatchadaAtianon/apprentice-helpdesk.git
cd apprentice-helpdesk

```
## 2. Create & Activate a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```
## 3. Install Dependencies
```bash
pip install -r requirements.txt
```
## 4. Set Up Environment Variables
Create a .env file in the root directory with the following contents:
```bash
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
```
## 5. Create tables, insert test data
This is where all user data lives so if you want to login then use user data from insert_data.py
```bash
python3 create_tables.py
python3 insert_data.py

```
## 6. Run Application
```bash
python3 main.py
```
## 7. Run tests and see coverage

```bash
coverage run -m pytest                                             
coverage report -m
```
