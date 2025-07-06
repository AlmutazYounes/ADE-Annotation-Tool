# ADE Annotation Tool

A Django-based web application for annotating medical text with drugs and adverse drug events (ADE). This tool provides an intuitive interface for Human-in-the-Loop (HITL) data annotation with real-time validation and entity management.

## Features

### 🚀 Core Functionality
- **Direct Text Highlighting**: Highlight text by dragging or double-clicking to label as Drug or Adverse Event
- **Interactive Entity Management**: Click highlighted entities to delete them
- **Real-time Validation**: Validate annotations with immediate visual feedback
- **JSONL Import/Export**: Support for both standard and entities format export
- **Search & Filter**: Find annotations by text content or validation status
- **Progress Tracking**: Visual progress bars and statistics dashboard

### 🎯 User Experience
- **Streamlined Interface**: Clean, minimal design focused on fast annotation
- **Keyboard Shortcuts**: Spacebar for quick validation
- **Auto-hide Validated**: Validated annotations disappear automatically
- **Responsive Design**: Works on desktop and tablet devices
- **Bootstrap UI**: Professional, modern interface

### 📊 Data Management
- **JSONL Support**: Import existing datasets in JSONL format
- **Dual Export Formats**: 
  - Standard: `{"text": "...", "drugs": [...], "adverse_events": [...]}`
  - Entities: `{"text": "...", "entities": [{"start": 0, "end": 10, "label": "DRUG"}]}`
- **Statistics Dashboard**: Track annotation progress and entity frequency
- **Data Validation**: Ensure data integrity during import/export

## Technology Stack

- **Backend**: Django 5.2.4, Python 3.x
- **Database**: SQLite (development), PostgreSQL-ready
- **Frontend**: Bootstrap 5.1.3, JavaScript (ES6+)
- **Styling**: Custom CSS with animations and responsive design

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/AlmutazYounes/ADE-Annotation-Tool.git
   cd ADE-Annotation-Tool
   ```

2. **Create virtual environment**
   ```bash
   python -m venv annotation_venv
   source annotation_venv/bin/activate  # On Windows: annotation_venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install django==5.2.4
   ```

4. **Setup database**
   ```bash
   cd data_annotation_tool
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser** (optional)
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Open http://127.0.0.1:8000/ in your browser
   - Admin panel: http://127.0.0.1:8000/admin/ (if superuser created)

## Usage

### Getting Started

1. **Import Data**: Use the Import button to upload your JSONL file with medical text data
2. **Annotate**: 
   - Highlight text (drag or double-click) to label as Drug or Adverse Event
   - Click existing highlighted entities to delete them
   - Use the Validate button when satisfied with annotations
3. **Export**: Download annotations in your preferred format (standard or entities)

### Data Format

**Input JSONL** (each line):
```json
{"text": "Patient experienced nausea after taking aspirin.", "drugs": [], "adverse_events": []}
```

**Standard Export**:
```json
{"text": "Patient experienced nausea after taking aspirin.", "drugs": ["aspirin"], "adverse_events": ["nausea"]}
```

**Entities Export**:
```json
{"text": "Patient experienced nausea after taking aspirin.", "entities": [{"start": 19, "end": 25, "label": "ADE"}, {"start": 38, "end": 45, "label": "DRUG"}]}
```

### Keyboard Shortcuts
- **Spacebar**: Validate the first unvalidated annotation
- **Click + Drag**: Select text to annotate
- **Double-click**: Select word to annotate

## Project Structure

```
ADE-Annotation-Tool/
├── data_annotation_tool/          # Django project root
│   ├── settings.py               # Django settings
│   ├── urls.py                   # URL routing
│   └── wsgi.py                   # WSGI configuration
├── annotation/                   # Main Django app
│   ├── models.py                 # TextAnnotation model
│   ├── views.py                  # Application views
│   ├── urls.py                   # App URL patterns
│   ├── admin.py                  # Django admin configuration
│   └── templates/annotation/     # HTML templates
├── extracted_data.jsonl          # Sample data file
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Models

### TextAnnotation
- `text` (TextField): The medical text to be annotated
- `drugs` (JSONField): List of drug names found in the text
- `adverse_events` (JSONField): List of adverse events found in the text
- `is_validated` (BooleanField): Whether the annotation has been validated
- `created_at` (DateTimeField): Timestamp of creation
- `updated_at` (DateTimeField): Timestamp of last update

## API Endpoints

- `/` - Main annotation interface
- `/annotation/import/` - JSONL import page
- `/annotation/export/` - Standard JSONL export
- `/annotation/export-entities/` - Entities format export
- `/annotation/stats/` - Statistics dashboard
- `/annotation/edit/<id>/` - AJAX endpoint for updating annotations
- `/admin/` - Django admin interface

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built for medical text annotation and adverse drug event detection
- Designed for Human-in-the-Loop machine learning workflows
- Optimized for rapid annotation validation

## Contact

Project Link: [https://github.com/AlmutazYounes/ADE-Annotation-Tool](https://github.com/AlmutazYounes/ADE-Annotation-Tool) 