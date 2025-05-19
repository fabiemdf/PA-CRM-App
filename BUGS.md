# Bug Tracker

This file lists known bugs and issues in the Monday Uploader app. Please append new bugs as they are discovered and update the status as they are fixed or worked around.

---

## 2024-05-19

### 1. Date Field Format Incompatibility
- **Description:**
  - The app originally stored date fields as `DateTime` in the database, but imported data often used non-ISO string formats (e.g., 'Apr 10, 2024').
  - This caused errors when loading claims, such as: `Invalid isoformat string: 'Apr 10, 2024'`.
- **Workaround:**
  - Changed all date fields in the database schema and SQLAlchemy model to `TEXT`/`String`.
  - Now, any date string can be stored, but there is no date validation or sorting.
- **Status:**
  - **Circumvented** (app runs, but date fields are not validated or parsed as dates).

### 2. Numeric Field 'N/A' Conversion Error
- **Description:**
  - During import, missing numeric values were set to `'N/A'` (string), causing float conversion errors when loading claims.
  - Error: `could not convert string to float: 'N/A'`.
- **Workaround:**
  - Updated loader to treat `'N/A'` and `None` as `0.0` for numeric fields.
- **Status:**
  - **Circumvented** (app runs, but missing numbers are always shown as 0.0).

---

**Please add new bugs below this line.** 