# Monday Uploader (PySide Edition)

A modern, feature-rich Monday.com integration application built with PySide6.

## Version History

### Stable 3 (Current)
- Added support for importing data for all available boards
- Fixed header row handling in Excel imports
- Added automatic board selection on startup
- Improved error handling for data imports
- Fixed UI issues with board display

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
- Data import from Excel files for all boards

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

### Importing Data

1. Click on "File" > "Import Board Data..." in the menu
2. Select the Excel file you want to import
3. Choose which board to import the data into from the popup menu
4. Specify which row contains the column headers (usually row 5)
5. The data will be imported and the board will be refreshed automatically

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