import pandas as pd
import matplotlib.pyplot as plt

class DataAnalyzer:
    def __init__(self, file_path):
        self.df = pd.read_csv(file_path)
        self.df['Date'] = pd.to_datetime(self.df['Date'])
    
    def query(self, question):
        if "top products" in question:
            return self.top_products()
        elif "sales over time" in question:
            return self.sales_trend()
        else:
            return "I can answer:\n- 'Show top products'\n- 'Show sales over time'"
    
    def top_products(self):
        top = self.df.groupby('Product').sum()['Quantity'].sort_values(ascending=False).head(5)
        top.plot(kind='bar', title='Top Selling Products')
        plt.savefig('top_products.png')
        return "Saved chart as top_products.png"
    
    def sales_trend(self):
        monthly = self.df.resample('M', on='Date').sum()['Quantity']
        monthly.plot(title='Monthly Sales Trend')
        plt.savefig('sales_trend.png')
        return "Saved chart as sales_trend.png"

# Test the analyzer
if __name__ == "__main__":
    analyzer = DataAnalyzer("sales_data.csv")  # Use your actual file
    print(analyzer.query("Show top products"))
    print(analyzer.query("Show sales over time"))