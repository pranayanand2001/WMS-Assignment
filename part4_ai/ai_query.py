import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
from typing import Tuple, Any, List

class DataAnalyzer:
    def __init__(self, file_path: str):
        """Initialize with a CSV file path"""
        self.df = None
        self.file_path = file_path
        try:
            if os.path.exists(file_path):
                self.df = pd.read_csv(file_path)
                self._preprocess_data()
            else:
                # Create sample data if file doesn't exist
                self.create_sample_data(file_path)
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            self.create_sample_data(file_path)

    def _preprocess_data(self):
        """Preprocess the loaded data"""
        if self.df is not None:
            # Convert date columns if they exist
            for col in self.df.columns:
                if col.lower() in ['date', 'timestamp', 'datetime']:
                    try:
                        self.df[col] = pd.to_datetime(self.df[col])
                    except:
                        continue

    def create_sample_data(self, file_path: str):
        """Create sample sales data"""
        # Create sample data
        data = {
            'Date': pd.date_range(start='2025-01-01', periods=100),
            'Product': [f'Product_{i%10}' for i in range(100)],
            'Quantity': np.random.randint(1, 50, 100),
            'Price': np.random.uniform(10, 100, 100).round(2)
        }
        self.df = pd.DataFrame(data)
        # Calculate total sales
        self.df['Total'] = (self.df['Quantity'] * self.df['Price']).round(2)
        # Save sample data
        self.df.to_csv(file_path, index=False)
        print(f"Created sample data file: {file_path}")

    def query(self, question: str) -> Tuple[pd.DataFrame, Any]:
        """Process a natural language query and return data with visualization"""
        question = question.lower()
        
        if "top" in question and ("products" in question or "selling" in question):
            return self._analyze_top_products()
        elif "sales" in question and "time" in question:
            return self._analyze_sales_trend()
        elif "revenue" in question or "sales" in question:
            return self._analyze_revenue()
        else:
            return self._analyze_basic_stats()
            
    def _analyze_top_products(self) -> Tuple[pd.DataFrame, Any]:
        """Analyze top selling products"""
        # Group by product and sum quantities
        product_sales = self.df.groupby('Product').agg({
            'Quantity': 'sum',
            'Total': 'sum'
        }).sort_values('Quantity', ascending=False)
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        product_sales['Quantity'].head(5).plot(kind='bar', ax=ax)
        plt.title('Top 5 Selling Products')
        plt.xlabel('Product')
        plt.ylabel('Total Quantity Sold')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        return product_sales.head(5), fig

    def _analyze_sales_trend(self) -> Tuple[pd.DataFrame, Any]:
        """Analyze sales trend over time"""
        # Group by date and calculate daily totals
        daily_sales = self.df.groupby('Date').agg({
            'Quantity': 'sum',
            'Total': 'sum'
        }).reset_index()
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(12, 6))
        daily_sales.plot(x='Date', y='Total', kind='line', ax=ax)
        plt.title('Sales Trend Over Time')
        plt.xlabel('Date')
        plt.ylabel('Total Sales ($)')
        plt.grid(True)
        plt.tight_layout()
        
        return daily_sales, fig

    def _analyze_revenue(self) -> Tuple[pd.DataFrame, Any]:
        """Analyze revenue by product"""
        # Calculate revenue metrics
        revenue_analysis = self.df.groupby('Product').agg({
            'Quantity': 'sum',
            'Total': 'sum',
            'Price': 'mean'
        }).round(2)
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        revenue_analysis['Total'].sort_values(ascending=True).plot(kind='barh', ax=ax)
        plt.title('Revenue by Product')
        plt.xlabel('Total Revenue ($)')
        plt.ylabel('Product')
        plt.tight_layout()
        
        return revenue_analysis, fig

    def _analyze_basic_stats(self) -> Tuple[pd.DataFrame, Any]:
        """Provide basic statistical analysis"""
        # Calculate basic stats
        stats = self.df.describe()
        
        # Create a simple visualization of the distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        self.df['Quantity'].hist(ax=ax, bins=20)
        plt.title('Distribution of Sales Quantities')
        plt.xlabel('Quantity')
        plt.ylabel('Frequency')
        plt.tight_layout()
        
        return stats, fig

    def get_sample_queries(self) -> List[str]:
        """Returns list of sample queries user can ask"""
        return [
            "Show me current inventory levels",
            "What are the top selling products?",
            "Show me low stock items",
            "Display all sales data"
        ]

# Example usage
if __name__ == "__main__":
    analyzer = DataAnalyzer('sales_data.csv')
    queries = [
        "Show me top selling products",
        "Show me sales over time",
        "Show me revenue by product",
        "Show me basic sales statistics"
    ]
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 50)
        df, fig = analyzer.query(query)
        print("\nData Results:")
        print(df)
        plt.figure(fig.number)
        plt.show()
        print("\nPress Enter to continue...")
        input()