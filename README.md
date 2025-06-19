# Warehouse Management System (WMS)

A comprehensive warehouse management system that integrates SKU mapping, combo product handling, inventory management, and sales data processing with a user-friendly web interface and Baserow integration.

## Tech Stack

### Backend
- **Python 3.x** - Core programming language
- **Flask** - Web framework
  - Flask-SQLAlchemy - Database ORM
  - Flask-Login - User authentication
- **Pandas** - Data processing and analysis
- **Baserow API** - Cloud database integration

### Frontend
- **HTML/CSS** - Structure and styling
- **Bootstrap 5** - UI framework
- **Font Awesome** - Icons
- **JavaScript** - Client-side interactivity
- **Chart.js** - Data visualization

## Key Features

1. **SKU Mapping System**
   - Flexible SKU column name detection
   - Validation and standardization
   - Support for combo products
   - Multi-warehouse inventory tracking

2. **Web Interface**
   - User authentication (register/login)
   - Drag-and-drop file upload
   - File type validation
   - Processing status tracking
   - Results visualization
   - Export to Baserow

3. **Data Processing**
   - Master mapping file processing
   - Combo product handling
   - Inventory management
   - Sales data processing
   - Real-time inventory updates

4. **Baserow Integration**
   - Automatic table creation
   - Smart field type inference
   - Batch data upload
   - Error handling and retry logic

## Project Structure

```
WMS-Assignment/
├── part1_gui/
│   └── sku_mapper.py           # Core SKU mapping and inventory logic
├── part2_database/             # Database scripts and schemas
├── part3_webapp/
│   ├── app.py                  # Flask application
│   ├── baserow_integration.py  # Baserow API client
│   ├── requirements.txt        # Python dependencies
│   ├── uploads/               # Uploaded files directory
│   └── templates/             # HTML templates
│       ├── base.html          # Base template
│       ├── index.html         # Dashboard
│       ├── login.html         # Login page
│       ├── register.html      # Registration page
│       ├── results.html       # Processing results
│       └── view_file.html     # File viewer
└── part4_ai/
    └── ai_query.py            # AI-powered data analysis
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd WMS-Assignment
   ```

2. **Set Up Python Environment**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Unix/MacOS:
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   cd part3_webapp
   pip install -r requirements.txt
   ```

4. **Configure Baserow**
   - Sign up at [Baserow.io](https://baserow.io)
   - Create a new database
   - Generate an API token
   - Update `app.py` with your credentials:
     ```python
     app.config['BASEROW_API_TOKEN'] = 'your-token-here'
     app.config['BASEROW_DATABASE_ID'] = your-database-id
     ```

5. **Initialize Database**
   ```bash
   python
   >>> from app import db
   >>> db.create_all()
   >>> exit()
   ```

6. **Run the Application**
   ```bash
   python app.py
   ```
   The application will be available at `http://localhost:5000`

## Usage Guide

1. **User Registration/Login**
   - Create a new account or login with existing credentials
   - Each user gets their own processing session

2. **File Upload Process**
   1. Upload Master Mapping file (CSV/Excel)
      - Contains SKU mappings and relationships
   2. Upload Combo Products file (optional)
      - Defines product combinations
   3. Upload Inventory file
      - Current stock levels by warehouse
   4. Upload Sales Data
      - Transactions to process

3. **Data Processing**
   - Click "Process All Data" when files are uploaded
   - System will:
     1. Validate SKUs
     2. Check inventory levels
     3. Process sales transactions
     4. Update inventory
     5. Generate results

4. **View and Export Results**
   - View processed data in the web interface
   - Download results as CSV/Excel
   - Export to Baserow for cloud storage

## Error Handling

The system includes comprehensive error handling for:
- Invalid file formats
- Missing required columns
- Invalid SKU formats
- Insufficient inventory
- API connection issues
- Database errors

## Development Tools Used

This project was developed using:
- **GitHub Copilot** - AI pair programming
- **VS Code** - Code editor with extensions:
  - Python
  - Flask
  - Git
  - Excel Viewer
- **Postman** - API testing
- **Git** - Version control

## Future Improvements

1. Add real-time inventory monitoring
2. Implement webhook notifications
3. Add more data visualization options
4. Enhance error reporting
5. Add bulk operation support
6. Implement caching for better performance


## Contributors

- Pranay
- GitHub Copilot (AI Assistant)
