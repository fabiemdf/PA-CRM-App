"""
Board configuration and mappings.
"""

# Default boards for offline mode
DEFAULT_BOARDS = {
    "Claims": "8903072880",
    "Clients": "8768750185",
    "Public Adjusters": "9000027904",
    "Employees": "9000122678",
    "Notes": "8968042746",
    "Documents": "8769212922",
    "Damage Estimates": "8769684040",
    "Communications": "8769967973",
    "Leads": "8778422410",
    "Tasks": "8792210214",
    "Insurance Companies": "8792259332",
    "Contacts": "8792441338",
    "Marketing Activities": "8792459115",
    "Insurance Representatives": "8876787198",
    "Police Report": "8884671005",
    "Weather Reports": "9123456789"
}

# Mapping of board names to their database models
BOARD_MODEL_MAP = {
    "Claims": "Claim",
    "Clients": "Client",
    "Public Adjusters": "PublicAdjuster",
    "Employees": "Employee",
    "Notes": "Note",
    "Documents": "Document",
    "Damage Estimates": "DamageEstimate",
    "Communications": "Communication",
    "Leads": "Lead",
    "Tasks": "Task",
    "Insurance Companies": "InsuranceCompany",
    "Contacts": "Contact",
    "Marketing Activities": "MarketingActivity",
    "Insurance Representatives": "InsuranceRepresentative",
    "Police Report": "PoliceReport",
    "Weather Reports": "WeatherReport"
} 