import pandas as pd
import re
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class SKUMapper:
    def __init__(self):
        self.master_map = {}
        self.combo_products = {}
        self.inventory = {}  # Format: {'warehouse': {'msku': quantity}}
        self.warehouse_list = set()  # To keep track of all warehouses
    
    def load_master_mapping(self, file_path):
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Check if the required columns exist (case-insensitive)
            columns = df.columns.str.upper()
            actual_sku_col = None
            actual_msku_col = None
            
            for col in df.columns:
                if col.upper() == 'SKU':
                    actual_sku_col = col
                elif col.upper() == 'MSKU':
                    actual_msku_col = col
            
            if actual_sku_col is None or actual_msku_col is None:
                message = f"Error: Required columns not found.\nAvailable columns: {', '.join(df.columns)}\n"
                message += "Please ensure your file has 'SKU' and 'MSKU' columns (case-sensitive)."
                raise ValueError(message)
            
            self.master_map = dict(zip(df[actual_sku_col], df[actual_msku_col]))
            
        except pd.errors.EmptyDataError:
            raise ValueError("The file is empty")
        except Exception as e:
            raise ValueError(f"Error loading file: {str(e)}")
    
    def validate_sku(self, sku):
        return bool(re.match(r'^[A-Z0-9_-]{3,20}$', sku))
    
    def map_sku(self, sku):
        if not self.validate_sku(sku):
            return "INVALID_FORMAT"
            
        # Check if this SKU is part of any combo
        for combo_id, combo_skus in self.combo_products.items():
            if sku in combo_skus:
                return f"{combo_id} (Part of combo)"
                
        return self.master_map.get(sku, "UNMAPPED")
    
    def add_combo(self, combo_id, skus):
        self.combo_products[combo_id] = [self.map_sku(sku) for sku in skus]
    
    def load_combo_mapping(self, file_path):
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Find all columns that contain SKU in their name
            sku_cols = [col for col in df.columns if 'SKU' in col.upper()]
            
            if not sku_cols:
                message = f"Error: No SKU columns found.\nAvailable columns: {', '.join(df.columns)}\n"
                message += "Please ensure your combo file has columns like SKU1, SKU2, etc."
                raise ValueError(message)
            
            # Process each row to create combo mappings
            for _, row in df.iterrows():
                skus = [row[col] for col in sku_cols if pd.notna(row[col])]  # Get non-empty SKUs
                if len(skus) > 1:  # Only create combo if there are at least 2 SKUs
                    combo_id = f"COMBO_{'-'.join(skus)}"  # Create a combo ID from the SKUs
                    self.add_combo(combo_id, skus)
            
            return len(self.combo_products)
            
        except pd.errors.EmptyDataError:
            raise ValueError("The file is empty")
        except Exception as e:
            raise ValueError(f"Error loading combo file: {str(e)}")
    
    def process_file(self, input_path):
        try:
            if input_path.endswith('.csv'):
                df = pd.read_csv(input_path)
            else:
                df = pd.read_excel(input_path)
            
            # Check if the required column exists (case-insensitive)
            columns = df.columns.str.upper()
            actual_sku_col = None
              # Try to find SKU column from common variations
            sku_column_names = ['SKU', 'Product_Id', 'ASIN', 'ProductId', 'Product ID', 'Item ID']
            for possible_name in sku_column_names:
                for col in df.columns:
                    if col.upper().replace('_', '').replace(' ', '') == possible_name.upper().replace('_', '').replace(' ', ''):
                        actual_sku_col = col
                        break
                if actual_sku_col is not None:
                    break
            
            if actual_sku_col is None:
                message = f"Error: No SKU column found. Looking for any of these columns: {', '.join(sku_column_names)}.\n"
                message += f"Available columns: {', '.join(df.columns)}\n"
                message += "Please ensure your sales data file has one of the supported SKU columns."
                raise ValueError(message)
            
            # Add MSKU column
            df['MSKU'] = df[actual_sku_col].apply(self.map_sku)
            return df
            
        except pd.errors.EmptyDataError:
            raise ValueError("The file is empty")
        except Exception as e:
            raise ValueError(f"Error processing file: {str(e)}")
    
    def load_inventory(self, file_path):
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            required_cols = ['msku', 'Opening Stock']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                message = f"Error: Required columns not found: {', '.join(missing_cols)}.\n"
                message += f"Available columns: {', '.join(df.columns)}"
                raise ValueError(message)
            
            # Initialize default warehouse if none specified
            warehouse = 'Main'
            self.warehouse_list.add(warehouse)
            
            # Initialize inventory for this warehouse
            if warehouse not in self.inventory:
                self.inventory[warehouse] = {}
            
            # Load inventory data
            for _, row in df.iterrows():
                msku = str(row['msku'])
                quantity = int(row['Opening Stock']) if pd.notna(row['Opening Stock']) else 0
                self.inventory[warehouse][msku] = quantity
            
            return len(self.inventory[warehouse])
            
        except pd.errors.EmptyDataError:
            raise ValueError("The file is empty")
        except Exception as e:
            raise ValueError(f"Error loading inventory: {str(e)}")
    
    def check_inventory(self, msku, warehouse='Main'):
        """Check inventory level for an MSKU in a specific warehouse"""
        if warehouse not in self.inventory or msku not in self.inventory[warehouse]:
            return 0
        return self.inventory[warehouse][msku]
    
    def update_inventory(self, msku, quantity, warehouse='Main'):
        """Update inventory level for an MSKU in a specific warehouse"""
        if warehouse not in self.inventory:
            self.inventory[warehouse] = {}
        if msku not in self.inventory[warehouse]:
            self.inventory[warehouse][msku] = 0
        self.inventory[warehouse][msku] += quantity
    
    def check_combo_inventory(self, combo_id):
        """Check if all parts of a combo are available"""
        if combo_id not in self.combo_products:
            return None
            
        min_available = float('inf')
        inventory_details = {}
        
        for msku in self.combo_products[combo_id]:
            total_available = sum(self.check_inventory(msku, wh) for wh in self.warehouse_list)
            inventory_details[msku] = {
                'total': total_available,
                'warehouses': {wh: self.check_inventory(msku, wh) for wh in self.warehouse_list}
            }
            min_available = min(min_available, total_available)
            
        return {
            'available_sets': min_available,
            'details': inventory_details
        }
    
    def subtract_from_inventory(self, msku, quantity, warehouse='Main'):
        """Subtract items from inventory, handling combos appropriately"""
        # Check if this is a combo
        for combo_id, combo_skus in self.combo_products.items():
            if msku == combo_id:
                # For combos, subtract each component
                available = self.check_combo_inventory(combo_id)
                if available and available['available_sets'] >= quantity:
                    for component_msku in combo_skus:
                        self.update_inventory(component_msku, -quantity, warehouse)
                    return True
                return False
        
        # For regular MSKUs
        current_qty = self.check_inventory(msku, warehouse)
        if current_qty >= quantity:
            self.update_inventory(msku, -quantity, warehouse)
            return True
        return False

class SKUMapperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SKU Mapper")
        self.mapper = SKUMapper()
        
        # Create UI
        self.create_widgets()
    
    def create_widgets(self):
        # File selection buttons frame
        file_frame = ttk.LabelFrame(self.root, text="File Operations")
        file_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Button(file_frame, text="Load Master Mapping", command=self.load_master).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(file_frame, text="Load Combo SKUs", command=self.load_combos).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Load Inventory", command=self.load_inventory_data).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(file_frame, text="Load Sales Data", command=self.load_sales).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(file_frame, text="Process & Save", command=self.process_data).grid(row=1, column=1, padx=5, pady=5)
        
        # Inventory view frame
        inventory_frame = ttk.LabelFrame(self.root, text="Inventory Status")
        inventory_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Inventory tree view
        self.inv_tree = ttk.Treeview(inventory_frame, columns=("MSKU", "Warehouse", "Quantity"), show="headings")
        self.inv_tree.heading("MSKU", text="MSKU")
        self.inv_tree.heading("Warehouse", text="Warehouse")
        self.inv_tree.heading("Quantity", text="Quantity")
        self.inv_tree.grid(row=0, column=0, padx=5, pady=5)
        
        # Status log
        log_frame = ttk.LabelFrame(self.root, text="Activity Log")
        log_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        self.log = tk.Text(log_frame, width=60, height=10)
        self.log.grid(row=0, column=0, padx=5, pady=5)
        
        # Preview table
        preview_frame = ttk.LabelFrame(self.root, text="Processing Preview")
        preview_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        self.tree = ttk.Treeview(preview_frame, columns=("SKU", "MSKU", "Status"), show="headings")
        self.tree.heading("SKU", text="SKU")
        self.tree.heading("MSKU", text="MSKU")
        self.tree.heading("Status", text="Status")
        self.tree.grid(row=0, column=0, padx=5, pady=5)
        
        # Manual operations frame
        manual_frame = ttk.LabelFrame(self.root, text="Manual Operations")
        manual_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(manual_frame, text="Combo Products (ID:SKU1,SKU2)").grid(row=0, column=0)
        self.combo_entry = ttk.Entry(manual_frame, width=50)
        self.combo_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(manual_frame, text="Add Combo", command=self.add_combo).grid(row=0, column=2)
    
    def log_message(self, message):
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
    
    def load_master(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.xlsx *.csv")])
        if file_path:
            try:
                self.mapper.load_master_mapping(file_path)
                self.log_message(f"Loaded master mapping: {len(self.mapper.master_map)} items")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                self.log_message(f"Error: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
                self.log_message(f"Error: {str(e)}")
    
    def load_combos(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.xlsx *.csv")])
        if file_path:
            try:
                num_combos = self.mapper.load_combo_mapping(file_path)
                self.log_message(f"Loaded combo mappings: {num_combos} combinations")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                self.log_message(f"Error: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
                self.log_message(f"Error: {str(e)}")
    
    def load_sales(self):
        self.sales_file = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.xlsx *.csv")])
        if self.sales_file:
            self.log_message(f"Sales data loaded: {os.path.basename(self.sales_file)}")
    
    def add_combo(self):
        combo_str = self.combo_entry.get()
        if ":" in combo_str:
            combo_id, skus_str = combo_str.split(":")
            skus = [s.strip() for s in skus_str.split(",")]
            self.mapper.add_combo(combo_id, skus)
            self.log_message(f"Added combo: {combo_id} = {skus}")
    
    def load_inventory_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.xlsx *.csv")])
        if file_path:
            try:
                num_items = self.mapper.load_inventory(file_path)
                self.log_message(f"Loaded inventory data: {num_items} items")
                self.update_inventory_display()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                self.log_message(f"Error: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
                self.log_message(f"Error: {str(e)}")
    
    def update_inventory_display(self):
        # Clear current display
        for item in self.inv_tree.get_children():
            self.inv_tree.delete(item)
        
        # Add all inventory items
        for warehouse in self.mapper.inventory:
            for msku, quantity in self.mapper.inventory[warehouse].items():
                self.inv_tree.insert("", "end", values=(msku, warehouse, quantity))
    
    def process_data(self):
        if not hasattr(self, 'sales_file'):
            messagebox.showerror("Error", "Load sales data first!")
            return
        
        if not self.mapper.master_map:
            messagebox.showerror("Error", "Load master mapping file first!")
            return
            
        if not self.mapper.inventory:
            messagebox.showerror("Error", "Load inventory data first!")
            return
        
        output_file = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")]
        )
        
        if output_file:
            try:
                # Load and process sales data
                if self.sales_file.endswith('.csv'):
                    df = pd.read_csv(self.sales_file)
                else:
                    df = pd.read_excel(self.sales_file)
                
                # Add MSKU column and inventory status
                df['MSKU'] = df['SKU'].apply(self.mapper.map_sku)
                df['Inventory_Status'] = df.apply(self.check_and_update_inventory, axis=1)
                
                # Save processed data
                if output_file.endswith('.csv'):
                    df.to_csv(output_file, index=False)
                else:
                    df.to_excel(output_file, index=False)
                
                # Update display
                self.update_inventory_display()
                
                # Show preview
                for row in self.tree.get_children():
                    self.tree.delete(row)
                for _, row in df.head(10).iterrows():
                    self.tree.insert("", "end", values=(row['SKU'], row['MSKU'], row['Inventory_Status']))
                
                # Log results
                self.log_message(f"File saved: {output_file}")
                self.log_message(f"Processed {len(df)} records")
                self.log_message(f"Inventory updated")
                
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                self.log_message(f"Error: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
                self.log_message(f"Error: {str(e)}")
    
    def check_and_update_inventory(self, row):
        """Check inventory and update if available"""
        try:
            quantity = int(row['Quantity']) if 'Quantity' in row else 1
            msku = row['MSKU']
            
            # Skip invalid MSKUs
            if msku in ['INVALID_FORMAT', 'UNMAPPED']:
                return 'Invalid SKU'
            
            # Handle combos
            if 'COMBO_' in str(msku):
                combo_status = self.mapper.check_combo_inventory(msku)
                if combo_status and combo_status['available_sets'] >= quantity:
                    # Subtract from inventory
                    self.mapper.subtract_from_inventory(msku, quantity)
                    return f'Processed (Combo - {quantity} sets)'
                else:
                    return 'Insufficient Combo Parts'
            
            # Handle regular SKUs
            total_available = sum(self.mapper.check_inventory(msku, wh) for wh in self.mapper.warehouse_list)
            if total_available >= quantity:
                # Find warehouse with enough inventory
                for warehouse in self.mapper.warehouse_list:
                    if self.mapper.check_inventory(msku, warehouse) >= quantity:
                        self.mapper.subtract_from_inventory(msku, quantity, warehouse)
                        return f'Processed ({warehouse})'
                
                # If no single warehouse has enough, handle split fulfillment
                remaining = quantity
                warehouses_used = []
                for warehouse in self.mapper.warehouse_list:
                    avail = self.mapper.check_inventory(msku, warehouse)
                    if avail > 0:
                        use_qty = min(avail, remaining)
                        self.mapper.subtract_from_inventory(msku, use_qty, warehouse)
                        remaining -= use_qty
                        warehouses_used.append(warehouse)
                        if remaining == 0:
                            break
                return f'Split across {", ".join(warehouses_used)}'
            else:
                return f'Insufficient Stock (Need: {quantity}, Have: {total_available})'
        except Exception as e:
            return f'Error: {str(e)}'

def main():
    root = tk.Tk()
    app = SKUMapperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()