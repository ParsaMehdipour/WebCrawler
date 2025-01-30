# 🌐 WebCrawler

A powerful web crawler designed to scrape e-commerce websites and extract valuable data such as product prices, images, sellers, and more.

---

## 🚀 Features

✅ Crawl e-commerce websites to gather product information.  
✅ Extract product details like prices, images, and seller information.  
✅ Store extracted data in a PostgreSQL database.  
✅ Optimized for efficiency and scalability.

---

## 🛠️ Requirements

- **Python 3.x**
- **Scrapy Framework**
- **PostgreSQL**
- **Docker (Optional, for containerized deployment)**

---

## 📦 Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/ParsaMehdipour/WebCrawler.git
cd WebCrawler
```

### 2️⃣ Set Up a Virtual Environment
```bash
python -m venv venv
```

### 3️⃣ Activate the Virtual Environment
- On **Linux/macOS**:
  ```bash
  source venv/bin/activate
  ```
- On **Windows**:
  ```bash
  venv\Scripts\activate
  ```

### 4️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### 🛢️ PostgreSQL Setup
1. Ensure PostgreSQL is installed and running.
2. Create a database and user for the application.

### 🔧 Database Connection Configuration
Modify the connection settings in the code:
```python
self.connection = psycopg2.connect(
    host='localhost',
    user='your_username',
    password='your_password',
    database='your_database'
)
```

---

## 🚴 Usage

### 🐳 Running with Docker
#### 1️⃣ Build the Docker image
```bash
docker build -t webcrawler .
```

#### 2️⃣ Run the Docker container
```bash
docker-compose up
```

---

## 📜 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! If you find any bugs or have feature requests, please open an issue or submit a pull request. 🚀

🎯 Happy Crawling! 🕷️

