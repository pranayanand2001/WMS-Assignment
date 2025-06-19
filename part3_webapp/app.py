from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
import os
from datetime import datetime
import sys
import requests
from typing import List, Dict, Any
from baserow_integration import BaserowClient, prepare_fields_from_dataframe, prepare_rows_from_dataframe

# Add parent directory to path to import SKUMapper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from part1_gui.sku_mapper import SKUMapper

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Baserow configuration
# Replace with your new token from Baserow settings
app.config['BASEROW_API_TOKEN'] = 'vPBS1xTy6whr1PwhP1vqp7ZSfTuIBklk'  
app.config['BASEROW_DATABASE_ID'] = 244113  

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_user_session():
    if current_user.is_authenticated:
        if current_user.id not in user_sessions:
            user_sessions[current_user.id] = ProcessingSession()
        return user_sessions[current_user.id]
    return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        uploads = Upload.query.filter_by(user_id=current_user.id).order_by(Upload.timestamp.desc()).all()
        session = get_user_session()
        return render_template('index.html', uploads=uploads, session=session)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    if current_user.id in user_sessions:
        del user_sessions[current_user.id]
    logout_user()
    return redirect(url_for('login'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    file_type = request.form.get('file_type')
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow()
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp.strftime('%Y%m%d%H%M%S')}_{filename}")
        file.save(file_path)
        
        # Create upload record
        upload = Upload(
            filename=filename,
            user_id=current_user.id,
            file_type=file_type,
            timestamp=timestamp
        )
        db.session.add(upload)
        db.session.commit()
        
        # Process file based on type
        session = get_user_session()
        try:
            if file_type == 'master':
                session.sku_mapper.load_master_mapping(file_path)
                session.has_master = True
                upload.status = 'Processed successfully'
            elif file_type == 'combo':
                session.sku_mapper.load_combo_mapping(file_path)
                session.has_combo = True
                upload.status = 'Processed successfully'
            elif file_type == 'inventory':
                session.sku_mapper.load_inventory(file_path)
                session.has_inventory = True
                upload.status = 'Processed successfully'
            elif file_type == 'sales':
                session.last_processed_file = file_path
                session.has_sales = True
                upload.status = 'Ready for processing'
        except Exception as e:
            upload.status = f'Error: {str(e)}'
            flash(f'Error processing file: {str(e)}', 'error')
        
        db.session.commit()
        flash('File uploaded successfully', 'success')
        return redirect(url_for('index'))
    
    flash('Invalid file type', 'error')
    return redirect(url_for('index'))

@app.route('/process', methods=['POST'])
@login_required
def process_data():
    session = get_user_session()
    if not all([session.has_master, session.has_inventory, session.has_sales]):
        flash('Please upload all required files first', 'error')
        return redirect(url_for('index'))
    
    try:
        # Process the sales data
        df = session.sku_mapper.process_file(session.last_processed_file)
        df['Inventory_Status'] = df.apply(lambda row: check_and_update_inventory(session.sku_mapper, row), axis=1)
        
        # Save processed file
        timestamp = datetime.utcnow()
        output_filename = f"processed_{timestamp.strftime('%Y%m%d%H%M%S')}.xlsx"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        df.to_excel(output_path, index=False)
        
        # Create upload record for processed file
        upload = Upload(
            filename=output_filename,
            user_id=current_user.id,
            file_type='processed',
            processed=True,
            status='Processing complete'
        )
        db.session.add(upload)
        db.session.commit()
        
        flash('Data processed successfully', 'success')
    except Exception as e:
        flash(f'Error processing data: {str(e)}', 'error')
    
    return redirect(url_for('index'))

def check_and_update_inventory(mapper, row):
    try:
        quantity = int(row['Quantity']) if 'Quantity' in row else 1
        msku = row['MSKU']
        
        if msku in ['INVALID_FORMAT', 'UNMAPPED']:
            return 'Invalid SKU'
        
        if 'COMBO_' in str(msku):
            combo_status = mapper.check_combo_inventory(msku)
            if combo_status and combo_status['available_sets'] >= quantity:
                mapper.subtract_from_inventory(msku, quantity)
                return f'Processed (Combo - {quantity} sets)'
            return 'Insufficient Combo Parts'
        
        total_available = sum(mapper.check_inventory(msku, wh) for wh in mapper.warehouse_list)
        if total_available >= quantity:
            for warehouse in mapper.warehouse_list:
                if mapper.check_inventory(msku, warehouse) >= quantity:
                    mapper.subtract_from_inventory(msku, quantity, warehouse)
                    return f'Processed ({warehouse})'
            
            remaining = quantity
            warehouses_used = []
            for warehouse in mapper.warehouse_list:
                avail = mapper.check_inventory(msku, warehouse)
                if avail > 0:
                    use_qty = min(avail, remaining)
                    mapper.subtract_from_inventory(msku, use_qty, warehouse)
                    remaining -= use_qty
                    warehouses_used.append(warehouse)
                    if remaining == 0:
                        break
            return f'Split across {", ".join(warehouses_used)}'
        return f'Insufficient Stock (Need: {quantity}, Have: {total_available})'
    except Exception as e:
        return f'Error: {str(e)}'

# User model for authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    uploads = db.relationship('Upload', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Model to track file uploads
class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # master, combo, inventory, or sales
    processed = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(120), default='Uploaded')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class ProcessingSession:
    def __init__(self):
        self.sku_mapper = SKUMapper()
        self.has_master = False
        self.has_combo = False
        self.has_inventory = False
        self.has_sales = False
        self.last_processed_file = None

# Store processing sessions for each user
user_sessions = {}

@app.route('/download/<filename>')
def download_file(filename):
    """Download a processed file."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/view/<filename>')
def view_file(filename):
    """View a processed file in the browser."""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Convert DataFrame to HTML table with Bootstrap classes
        table_html = df.to_html(classes=['table', 'table-striped', 'table-bordered', 'table-hover'],
                               index=False, escape=False)
        
        return render_template('view_file.html', table=table_html, filename=filename)
    except Exception as e:
        flash(f'Error viewing file: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/export_to_baserow/<filename>')
def export_to_baserow(filename: str):
    """Export a processed file to Baserow."""
    if not app.config.get('BASEROW_API_TOKEN') or not app.config.get('BASEROW_DATABASE_ID'):
        flash('Baserow API token or Database ID not configured. Please check your configuration.', 'error')
        return redirect(url_for('view_file', filename=filename))

    try:
        # Read the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            flash('File not found.', 'error')
            return redirect(url_for('index'))

        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        if df.empty:
            flash('No data to export.', 'error')
            return redirect(url_for('view_file', filename=filename))
        
        # Initialize Baserow client with better error handling
        try:
            client = BaserowClient(
                api_token=str(app.config['BASEROW_API_TOKEN']),
                database_id=int(app.config['BASEROW_DATABASE_ID'])
            )
        except ValueError as e:
            flash(f'Baserow Authentication Error: {str(e)}. Please check your API token configuration.', 'error')
            return redirect(url_for('view_file', filename=filename))
        
        # Prepare fields and rows
        fields = prepare_fields_from_dataframe(df)
        rows = prepare_rows_from_dataframe(df)
        
        if not rows:
            flash('No data to export.', 'error')
            return redirect(url_for('view_file', filename=filename))
        
        # Create or get table with proper error handling
        table_name = f"Processed_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        flash(f'Creating table {table_name}...', 'info')
        
        try:
            table_id = client.get_or_create_table(
                int(app.config['BASEROW_DATABASE_ID']),
                table_name,
                fields
            )
        except ValueError as e:
            flash(f'Baserow Error: {str(e)}', 'error')
            if "Invalid API token" in str(e):
                flash('Please check your Baserow API token in the configuration.', 'error')
            elif "Database" in str(e) and "not found" in str(e):
                flash('Please verify your Baserow Database ID in the configuration.', 'error')
            return redirect(url_for('view_file', filename=filename))
        
        # Insert data in batches
        batch_size = 100
        total_rows = len(rows)
        
        for i in range(0, total_rows, batch_size):
            batch = [{k: str(v) if pd.isna(v) else v for k, v in row.items()} 
                    for row in rows[i:i + batch_size]]
            client.create_rows(table_id, batch)
            flash(f'Exported {min(i + batch_size, total_rows)} of {total_rows} rows...', 'info')
        
        # Final success message
        flash(f'Successfully exported {total_rows} rows to Baserow table: {table_name}', 'success')
        
        # Create a record of the export
        export_record = Upload()
        export_record.filename = f"baserow_export_{filename}"
        export_record.user_id = current_user.id if current_user.is_authenticated else 1
        export_record.file_type = 'baserow_export'
        export_record.processed = True
        export_record.status = f'Exported to Baserow table: {table_name}'
        export_record.timestamp = datetime.utcnow()
        
        db.session.add(export_record)
        db.session.commit()
        
        # Return to the view page
        return redirect(url_for('view_file', filename=filename))

    except requests.exceptions.RequestException as e:
        # Handle Baserow API errors
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_message = error_data.get('error', str(e))
            except:
                error_message = e.response.text or str(e)
        else:
            error_message = str(e)
        flash(f'Baserow API Error: {error_message}', 'error')
        return redirect(url_for('view_file', filename=filename))
        
    except Exception as e:
        # Handle other errors
        flash(f'Error exporting to Baserow: {str(e)}', 'error')
        return redirect(url_for('view_file', filename=filename))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)