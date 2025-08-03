<div align="center">

# 🏥 Medical Text Annotation Tool

### Human-in-the-Loop Data Annotation for Adverse Drug Events

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2.4-green?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-Compatible-orange?style=for-the-badge)](https://huggingface.co)

[🚀 Quick Start](#-installation) • [📖 Documentation](#-usage) • [🎯 Features](#-features) • [🤝 Contributing](#-contributing)

</div>

---

## 🌟 Overview

A powerful, intuitive Django-based web application designed for **medical text annotation** with a focus on **Adverse Drug Events (ADE)** and **drug entity recognition**. Built for researchers, data scientists, and medical professionals who need to create high-quality labeled datasets for machine learning models.

### 🎯 Perfect For
- 🔬 **Medical Research**: Pharmacovigilance and drug safety studies
- 🤖 **ML Training**: Creating labeled datasets for NER models
- 📊 **Data Science**: HITL annotation workflows
- 🏥 **Healthcare**: Clinical text analysis and research

## ✨ Features

### 🚀 Core Annotation Capabilities
- **🖱️ Intuitive Text Selection**: Drag-to-highlight or double-click for instant labeling
- **🏷️ Dual Entity Types**: Drugs and Adverse Drug Events with visual distinction
- **⚡ Real-time Validation**: Instant feedback with keyboard shortcuts (Spacebar)
- **🔄 Interactive Management**: Click entities to remove, seamless editing workflow
- **📱 Responsive Design**: Works flawlessly on desktop, tablet, and mobile

### 📊 Advanced Data Management
- **📥 JSONL Import/Export**: Industry-standard format support
- **🔄 Dual Export Formats**:
  - **Standard**: `{"text": "...", "drugs": [...], "adverse_events": [...]}`
  - **Entities**: `{"text": "...", "entities": [{"start": 0, "end": 10, "label": "DRUG"}]}`
- **📈 Progress Tracking**: Real-time statistics and completion metrics
- **🔍 Smart Filtering**: Search by content, validation status, or entity types
- **☁️ Hugging Face Integration**: Direct upload to HF Hub for sharing datasets

### 🎨 User Experience
- **⚡ Lightning Fast**: Optimized for rapid annotation workflows
- **🎯 Focused Interface**: Distraction-free design for maximum productivity
- **⌨️ Keyboard Shortcuts**: Power-user features for efficiency
- **🎨 Modern UI**: Bootstrap 5 with custom animations and styling
- **🔄 Auto-hide Validated**: Completed annotations fade away automatically

## 🛠️ Technology Stack

<div align="center">

| Component | Technology | Version |
|-----------|------------|---------|
| **Backend** | ![Django](https://img.shields.io/badge/Django-092E20?style=flat&logo=django&logoColor=white) | 5.2.4 |
| **Language** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) | 3.8+ |
| **Database** | ![SQLite](https://img.shields.io/badge/SQLite-07405E?style=flat&logo=sqlite&logoColor=white) | Built-in |
| **Frontend** | ![Bootstrap](https://img.shields.io/badge/Bootstrap-563D7C?style=flat&logo=bootstrap&logoColor=white) | 5.1.3 |
| **JavaScript** | ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black) | ES6+ |
| **Integration** | ![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-FFD21E?style=flat) | Hub API |

</div>

## 🚀 Installation

### 📋 Prerequisites

- **Python 3.8+** ([Download](https://python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **pip** (included with Python)

### ⚡ Quick Setup

```bash
# 1️⃣ Clone the repository
git clone https://github.com/AlmutazYounes/ADE-Annotation-Tool.git
cd ADE-Annotation-Tool

# 2️⃣ Create and activate virtual environment
python -m venv annotation_venv

# On macOS/Linux:
source annotation_venv/bin/activate

# On Windows:
annotation_venv\Scripts\activate

# 3️⃣ Install all dependencies
pip install -r requirements.txt

# 4️⃣ Setup database
python manage.py makemigrations
python manage.py migrate

# 5️⃣ Create admin user (optional)
python manage.py createsuperuser

# 6️⃣ Start the development server
python manage.py runserver
```

### 🌐 Access Your Application

- **Main App**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **API Docs**: http://127.0.0.1:8000/annotation/

### 🐳 Docker Setup (Alternative)

```bash
# Coming soon - Docker support planned for v2.0
```

## 📖 Usage

### 🎬 Demo & Screenshots

> **📸 Screenshots coming soon!** We're preparing visual guides to showcase the annotation interface.

<details>
<summary>🖼️ Click to view interface previews</summary>

```
🔄 Main Annotation Interface    📊 Statistics Dashboard    ☁️ Hugging Face Upload
     [Coming Soon]                  [Coming Soon]              [Coming Soon]
```

</details>

### 🚀 Quick Start Guide

#### 1️⃣ **Import Your Data**
```bash
# Prepare your JSONL file
echo '{"text": "Patient experienced nausea after taking aspirin.", "drugs": [], "adverse_events": []}' > sample_data.jsonl
```
- Click **"Import"** button in the interface
- Upload your JSONL file with medical texts
- Data is automatically validated and loaded

#### 2️⃣ **Start Annotating**
- **🖱️ Drag to select** text spans for annotation
- **🖱️ Double-click** to select individual words
- **🏷️ Choose entity type**: Drug or Adverse Event
- **❌ Click entities** to remove them
- **✅ Press Spacebar** to validate annotations

#### 3️⃣ **Export & Share**
- **📥 Standard Format**: For training ML models
- **📥 Entities Format**: For NER tasks
- **☁️ Hugging Face**: Direct upload to HF Hub

### 📊 Data Formats

#### Input Format (JSONL)
```json
{"text": "Patient experienced nausea after taking aspirin.", "drugs": [], "adverse_events": []}
{"text": "Headache occurred following ibuprofen administration.", "drugs": [], "adverse_events": []}
```

#### Standard Export
```json
{
  "text": "Patient experienced nausea after taking aspirin.",
  "drugs": ["aspirin"],
  "adverse_events": ["nausea"],
  "is_validated": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Entities Export (NER Format)
```json
{
  "text": "Patient experienced nausea after taking aspirin.",
  "entities": [
    {"start": 19, "end": 25, "label": "ADE"},
    {"start": 38, "end": 45, "label": "DRUG"}
  ]
}
```

### ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Spacebar` | Validate current annotation |
| `Drag + Drop` | Select text for annotation |
| `Double Click` | Select word for annotation |
| `Click Entity` | Remove annotation |
| `Ctrl/Cmd + S` | Save progress |

### 🔄 Workflow Example

```mermaid
graph LR
    A[📥 Import JSONL] --> B[🖱️ Select Text]
    B --> C[🏷️ Label Entity]
    C --> D[✅ Validate]
    D --> E[📊 Review Stats]
    E --> F[📤 Export Data]
    F --> G[☁️ Share on HF Hub]
```

## 🏗️ Project Architecture

<details>
<summary>📁 Project Structure</summary>

```
ADE-Annotation-Tool/
├── 📁 data_annotation_tool/       # Django project root
│   ├── ⚙️ settings.py            # Configuration & database settings
│   ├── 🌐 urls.py                # Main URL routing
│   ├── 🚀 wsgi.py                # WSGI configuration for deployment
│   └── 📡 asgi.py                # ASGI configuration (async support)
├── 📁 annotation/                # Core annotation application
│   ├── 🗃️ models.py              # Data models (TextAnnotation, etc.)
│   ├── 👁️ views.py               # Business logic & API endpoints
│   ├── 🛣️ urls.py                # App-specific URL patterns
│   ├── ⚡ admin.py               # Django admin interface
│   ├── 📁 templates/             # HTML templates
│   ├── 📁 static/                # CSS, JS, images
│   └── 📁 migrations/            # Database schema changes
├── 📊 GOLD data/                 # Sample datasets
├── 📋 requirements.txt           # Python dependencies
├── 🗄️ db.sqlite3               # SQLite database (auto-generated)
└── 📖 README.md                 # This documentation
```

</details>

### 🗃️ Data Models

#### TextAnnotation Model
```python
class TextAnnotation(models.Model):
    text = models.TextField()                    # Medical text content
    drugs = models.JSONField(default=list)       # Identified drug entities
    adverse_events = models.JSONField(default=list)  # ADE entities
    is_validated = models.BooleanField(default=False)  # Validation status
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 🛣️ API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main annotation interface |
| `/annotation/import/` | GET/POST | JSONL data import |
| `/annotation/export/` | GET | Standard format export |
| `/annotation/export-entities/` | GET | NER format export |
| `/annotation/upload-hf/` | GET/POST | Hugging Face upload |
| `/annotation/stats/` | GET | Statistics dashboard |
| `/annotation/edit/<id>/` | POST | AJAX annotation updates |
| `/admin/` | GET | Django admin panel |

## 🚀 Deployment

### 🌐 Production Deployment

#### Option 1: Traditional Server (Ubuntu/CentOS)

```bash
# 1. Server setup
sudo apt update && sudo apt install python3 python3-pip nginx postgresql

# 2. Clone and setup
git clone https://github.com/AlmutazYounes/ADE-Annotation-Tool.git
cd ADE-Annotation-Tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn psycopg2-binary

# 3. Configure PostgreSQL
sudo -u postgres createdb annotation_db
sudo -u postgres createuser annotation_user

# 4. Update settings for production
export DJANGO_SETTINGS_MODULE=data_annotation_tool.settings
export DATABASE_URL=postgresql://annotation_user:password@localhost/annotation_db

# 5. Deploy
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn data_annotation_tool.wsgi:application --bind 0.0.0.0:8000
```

#### Option 2: Docker Deployment (Recommended)

```dockerfile
# Dockerfile (create this file)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "data_annotation_tool.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```bash
# Build and run
docker build -t medical-annotation-tool .
docker run -p 8000:8000 medical-annotation-tool
```

#### Option 3: Cloud Platforms

<details>
<summary>☁️ Platform-specific guides</summary>

**Heroku**
```bash
# Install Heroku CLI, then:
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
heroku run python manage.py migrate
```

**Railway**
```bash
# Connect GitHub repo to Railway
# Add environment variables in dashboard
# Deploy automatically on push
```

**DigitalOcean App Platform**
```yaml
# app.yaml
name: medical-annotation-tool
services:
- name: web
  source_dir: /
  github:
    repo: your-username/ADE-Annotation-Tool
    branch: main
  run_command: gunicorn data_annotation_tool.wsgi:application
```

</details>

### 🔧 Environment Variables

```bash
# .env file (create for production)
DEBUG=False
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/dbname
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 🛠️ Troubleshooting

### ❗ Common Issues & Solutions

<details>
<summary>🐛 Installation Problems</summary>

**Issue**: `ModuleNotFoundError: No module named 'django'`
```bash
# Solution: Ensure virtual environment is activated
source annotation_venv/bin/activate  # macOS/Linux
# or
annotation_venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

**Issue**: `huggingface_hub not found`
```bash
# Solution: Install missing dependency
pip install huggingface_hub==0.24.6
```

**Issue**: Database migration errors
```bash
# Solution: Reset migrations
rm -rf annotation/migrations/
python manage.py makemigrations annotation
python manage.py migrate
```

</details>

<details>
<summary>🔐 Authentication Issues</summary>

**Issue**: Hugging Face upload fails
- ✅ Verify token at https://huggingface.co/settings/tokens
- ✅ Ensure token has write permissions
- ✅ Check dataset name format (alphanumeric, hyphens, underscores only)

**Issue**: Admin panel access denied
```bash
# Solution: Create superuser
python manage.py createsuperuser
```

</details>

<details>
<summary>⚡ Performance Issues</summary>

**Issue**: Slow annotation loading
- ✅ Check database size (SQLite has limits)
- ✅ Consider PostgreSQL for large datasets
- ✅ Enable database indexing

**Issue**: Memory usage high
- ✅ Limit concurrent annotations
- ✅ Implement pagination for large datasets
- ✅ Use database connection pooling

</details>

### 📞 Getting Help

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/AlmutazYounes/ADE-Annotation-Tool/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/AlmutazYounes/ADE-Annotation-Tool/discussions)
- 📧 **Email**: [Contact maintainer](mailto:your-email@example.com)
- 📖 **Documentation**: [Wiki](https://github.com/AlmutazYounes/ADE-Annotation-Tool/wiki)

## 🤝 Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### 🚀 Quick Contribution Guide

1. **🍴 Fork** the repository
2. **🌿 Create** a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **💻 Make** your changes
4. **✅ Test** your changes
   ```bash
   python manage.py test
   ```
5. **📝 Commit** with a clear message
   ```bash
   git commit -m "✨ Add amazing feature for better UX"
   ```
6. **🚀 Push** to your branch
   ```bash
   git push origin feature/amazing-feature
   ```
7. **🔄 Open** a Pull Request

### 🎯 Contribution Areas

- 🐛 **Bug Fixes**: Help us squash bugs
- ✨ **New Features**: Add annotation capabilities
- 📚 **Documentation**: Improve guides and examples
- 🎨 **UI/UX**: Enhance the user interface
- 🔧 **Performance**: Optimize for speed and scale
- 🧪 **Testing**: Add test coverage
- 🌐 **Internationalization**: Add language support

### 📋 Development Setup

```bash
# 1. Fork and clone your fork
git clone https://github.com/YOUR-USERNAME/ADE-Annotation-Tool.git
cd ADE-Annotation-Tool

# 2. Set up development environment
python -m venv dev_env
source dev_env/bin/activate  # or dev_env\Scripts\activate on Windows
pip install -r requirements.txt

# 3. Set up pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install

# 4. Run tests
python manage.py test

# 5. Start development server
python manage.py runserver
```

### 🏷️ Commit Convention

We use [Conventional Commits](https://conventionalcommits.org/):

- `✨ feat:` New features
- `🐛 fix:` Bug fixes
- `📚 docs:` Documentation changes
- `🎨 style:` Code style changes
- `♻️ refactor:` Code refactoring
- `🧪 test:` Adding tests
- `⚡ perf:` Performance improvements

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Medical Text Annotation Tool Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 🙏 Acknowledgments

- 🏥 **Medical Community**: For inspiring this tool's development
- 🤗 **Hugging Face**: For providing excellent ML infrastructure
- 🐍 **Django Community**: For the robust web framework
- 🎨 **Bootstrap Team**: For the beautiful UI components
- 👥 **Contributors**: Everyone who has contributed to this project

### 🌟 Special Thanks

- **Pharmacovigilance Researchers**: For domain expertise and feedback
- **Data Scientists**: For ML workflow insights
- **Healthcare Professionals**: For real-world use case validation

## 📞 Contact & Support

<div align="center">

### 🔗 Links

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/AlmutazYounes/ADE-Annotation-Tool)
[![Issues](https://img.shields.io/badge/Issues-FF6B6B?style=for-the-badge&logo=github&logoColor=white)](https://github.com/AlmutazYounes/ADE-Annotation-Tool/issues)
[![Discussions](https://img.shields.io/badge/Discussions-4ECDC4?style=for-the-badge&logo=github&logoColor=white)](https://github.com/AlmutazYounes/ADE-Annotation-Tool/discussions)

### 📧 Maintainer

**Almutaz Younes**
📧 Email: [your-email@example.com](mailto:your-email@example.com)
🐙 GitHub: [@AlmutazYounes](https://github.com/AlmutazYounes)

</div>

---

<div align="center">

### 🌟 Star this repository if it helped you!

**Made with ❤️ for the medical research community**

[⬆️ Back to Top](#-medical-text-annotation-tool)

</div>