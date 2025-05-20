# Excel Files for Monday Uploader

This directory contains the Excel files used by the Monday Uploader application. Each Excel file corresponds to a specific board in the Monday.com workspace.

## Update for Stable 3 Release

In Stable 3, we've improved the Excel import functionality:

- Added support for importing data for all available boards
- Fixed header row handling to correctly process the data
- Enhanced error handling and validation
- Added user interface to select which row contains headers (usually row 5)
- Data validation to ensure proper formatting

## Required Files

The following Excel files are required for the application to function properly:

1. `PA_Claims_FPA_Claims.xlsx` - Claims board data
2. `Clients_FPA_Clients.xlsx` - Clients board data
3. `Public_Adjusters_FPA.xlsx` - Public Adjusters board data
4. `Employees_Group_Title.xlsx` - Employees board data
5. `Notes_Monday_Notes.xlsx` - Notes board data
6. `Insurance_Representatives_Fraser.xlsx` - Insurance Representatives board data
7. `Police_Report_Group_Title.xlsx` - Police Report board data
8. `Damage_Estimates_Fraser.xlsx` - Damage Estimates board data
9. `Communications_Fraser.xlsx` - Communications board data
10. `Leads_Group_Title.xlsx` - Leads board data
11. `Documents_Fraser.xlsx` - Documents board data
12. `Tasks_Group_Title.xlsx` - Tasks board data
13. `Insurance_Companies_Fraser.xlsx` - Insurance Companies board data
14. `Contacts_Business_Contacts.xlsx` - Contacts board data
15. `Marketing_Activities_This_week.xlsx` - Marketing Activities board data

## File Format

Each Excel file should follow these guidelines:

1. Headers typically start at row 5 in the provided Excel templates
2. Column headers should match the Monday.com board columns
3. Data should start immediately after the header row
4. Make sure there are no blank rows between headers and data

## Setup Instructions

1. Place all Excel files in this directory
2. Use the "Import Board Data..." option from the File menu to import each file
3. Select the appropriate board for each Excel file
4. Specify which row contains the column headers (typically row 5)
5. The application will import the data and refresh the board automatically

## Database Storage

Imported Excel data is stored in the SQLite database (monday_sync.db) in the root directory. This allows the application to:

1. Maintain data between sessions
2. Function in offline mode
3. Provide filtering, sorting, and searching capabilities
4. Support backup and restoration

## Troubleshooting

If you encounter issues with Excel file imports:

1. Check that the Excel file is in the correct format
2. Ensure you've selected the correct header row (usually row 5)
3. Verify that the data follows the expected structure
4. Check the application logs for specific error messages

## Note

The application will display all available boards on startup, even if no data has been imported yet. You can import data for any board using the File > Import Board Data... menu option. 