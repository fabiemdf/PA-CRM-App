# Monday Uploader (PySide Edition)

A modern, feature-rich Monday.com integration application built with PySide6.

## Features

- Modern PySide6-based user interface
- Dockable panels for flexible workspace layout
- Board management and item tracking
- Calendar integration
- Map view for location-based data
- Weather and news feeds
- Comprehensive feedback system
- Offline mode support
- Auto-sync capabilities

## Requirements

- Python 3.8+
- PySide6
- SQLAlchemy
- pandas
- Other dependencies listed in requirements.txt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/monday-uploader-pyside.git
cd monday-uploader-pyside
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python src/main.py
```

## Configuration

1. Create a `config.json` file in the project root with your Monday.com API key:
```json
{
    "api_key": "your_monday_api_key_here"
}
```

2. Configure additional settings in `settings.json`:
```json
{
    "auto_sync": true,
    "sync_interval": 300,
    "default_boards": {
        "Claims": "8903072880",
        "Clients": "8768750185"
    }
}
```

## Development

- Source code is organized in the `src` directory
- UI components are in `src/ui`
- Controllers are in `src/controllers`
- Models are in `src/models`
- Database initialization is in `src/database`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 