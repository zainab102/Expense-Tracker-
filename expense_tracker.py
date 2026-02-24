import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import tempfile
import pandas as pd

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "expense_tracker_mplconfig"))

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from fpdf import FPDF

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1200x800")

        # Data variables
        self.df = None
        self.filtered_df = None
        self.month_filter = tk.StringVar(value="All")
        self.search_var = tk.StringVar()
        self.budgets = {}  # Category budgets
        self.category_colors = {
            'Food': '#FF6B6B', 'Transportation': '#4ECDC4', 'Entertainment': '#45B7D1',
            'Utilities': '#96CEB4', 'Unknown': '#FECA57'
        }

        # Create GUI elements
        self.create_widgets()

    def create_widgets(self):
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load CSV", command=self.load_csv)
        file_menu.add_command(label="Export Summary to CSV", command=self.export_csv)
        file_menu.add_command(label="Export Report to PDF", command=self.export_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top frame for controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(control_frame, text="Month Filter:").pack(side=tk.LEFT, padx=(0, 5))
        month_combo = ttk.Combobox(control_frame, textvariable=self.month_filter, state="readonly")
        month_combo['values'] = ["All"] + [f"{i:02d}" for i in range(1, 13)]
        month_combo.pack(side=tk.LEFT, padx=(0, 10))
        month_combo.bind("<<ComboboxSelected>>", self.apply_filter)

        ttk.Label(control_frame, text="Search:").pack(side=tk.LEFT, padx=(10, 5))
        search_entry = ttk.Entry(control_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        search_entry.bind("<KeyRelease>", self.apply_filter)

        ttk.Button(control_frame, text="📂 Load Sample Data", command=self.load_sample).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="➕ Add Expense", command=self.add_expense).pack(side=tk.LEFT)

        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Dashboard tab
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        self.create_dashboard(dashboard_frame)

        # Summary tab
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="Summary")

        self.summary_text = tk.Text(summary_frame, wrap=tk.WORD, height=10)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Charts tab
        charts_frame = ttk.Frame(self.notebook)
        self.notebook.add(charts_frame, text="Charts")

        self.chart_canvas = tk.Canvas(charts_frame)
        self.chart_canvas.pack(fill=tk.BOTH, expand=True)

        # Data tab
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="Data")

        self.data_tree = ttk.Treeview(data_frame)
        scrollbar = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_dashboard(self, frame):
        # Dashboard with key metrics
        metrics_frame = ttk.Frame(frame)
        metrics_frame.pack(fill=tk.X, pady=10)

        self.total_label = ttk.Label(metrics_frame, text="Total Expenses: $0.00", font=("Arial", 16, "bold"))
        self.total_label.pack(side=tk.LEFT, padx=20)

        self.budget_status_label = ttk.Label(metrics_frame, text="Budget Status: On Track", font=("Arial", 12))
        self.budget_status_label.pack(side=tk.LEFT, padx=20)

        # Progress bars for categories
        self.progress_frame = ttk.Frame(frame)
        self.progress_frame.pack(fill=tk.X, pady=10)

        ttk.Label(self.progress_frame, text="Category Budget Progress:").pack(anchor=tk.W)
        self.progress_bars_container = ttk.Frame(self.progress_frame)
        self.progress_bars_container.pack(fill=tk.X, pady=(5, 0))

        self.progress_bars = {}

        # Budget setting
        budget_frame = ttk.Frame(frame)
        budget_frame.pack(fill=tk.X, pady=10)

        ttk.Label(budget_frame, text="Set Budgets:").pack(anchor=tk.W)
        self.budget_entries = {}
        for category in self.category_colors.keys():
            cat_frame = ttk.Frame(budget_frame)
            cat_frame.pack(fill=tk.X, pady=2)
            ttk.Label(cat_frame, text=f"{category}:").pack(side=tk.LEFT)
            entry = ttk.Entry(cat_frame, width=10)
            entry.pack(side=tk.LEFT, padx=(5, 0))
            ttk.Button(cat_frame, text="Set", command=lambda c=category, e=entry: self.set_budget(c, e)).pack(side=tk.LEFT, padx=(5, 0))
            self.budget_entries[category] = entry

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                self.df = pd.read_csv(file_path)
                self.clean_data()
                self.apply_filter()
                messagebox.showinfo("Success", "CSV loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV: {str(e)}")

    def load_sample(self):
        sample_path = os.path.join(os.path.dirname(__file__), "sample_expenses.csv")
        try:
            self.df = pd.read_csv(sample_path)
            self.clean_data()
            self.apply_filter()
            messagebox.showinfo("Success", "Sample data loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load sample data: {str(e)}")

    def clean_data(self):
        if self.df is not None:
            # Convert Date to datetime
            self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce')
            # Fill missing values
            self.df['Amount'] = pd.to_numeric(self.df['Amount'], errors='coerce')
            self.df['Category'] = self.df['Category'].fillna('Unknown')
            self.df['Description'] = self.df['Description'].fillna('')
            # Drop rows with missing essential data
            self.df = self.df.dropna(subset=['Date', 'Amount'])

    def apply_filter(self, event=None):
        if self.df is not None:
            if self.month_filter.get() == "All":
                self.filtered_df = self.df.copy()
            else:
                month = int(self.month_filter.get())
                self.filtered_df = self.df[self.df['Date'].dt.month == month].copy()

            # Apply search filter
            search_term = self.search_var.get().lower()
            if search_term:
                self.filtered_df = self.filtered_df[
                    self.filtered_df['Description'].str.lower().str.contains(search_term) |
                    self.filtered_df['Category'].str.lower().str.contains(search_term)
                ]

            self.update_summary()
            self.update_charts()
            self.update_data_view()
            self.update_dashboard()
        else:
            self.filtered_df = None
            self.update_dashboard()

    def update_summary(self):
        if self.filtered_df is not None and not self.filtered_df.empty:
            total_expenses = self.filtered_df['Amount'].sum()
            category_summary = self.filtered_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
            monthly_summary = self.filtered_df.groupby(self.filtered_df['Date'].dt.to_period('M'))['Amount'].sum()

            summary = f"Total Expenses: ${total_expenses:.2f}\n\n"
            summary += "Expenses by Category:\n"
            for category, amount in category_summary.items():
                summary += f"{category}: ${amount:.2f}\n"

            summary += "\nMonthly Breakdown:\n"
            for period, amount in monthly_summary.items():
                summary += f"{period}: ${amount:.2f}\n"

            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, summary)
        else:
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, "No data to display.")

    def update_charts(self):
        if self.filtered_df is not None and not self.filtered_df.empty:
            # Clear previous charts
            for widget in self.chart_canvas.winfo_children():
                widget.destroy()

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))

            # Bar chart: Expenses by category
            category_sum = self.filtered_df.groupby('Category')['Amount'].sum()
            ax1.bar(category_sum.index, category_sum.values)
            ax1.set_title('Expenses by Category')
            ax1.set_ylabel('Amount ($)')
            ax1.tick_params(axis='x', rotation=45)

            # Pie chart: Category distribution
            ax2.pie(category_sum.values, labels=category_sum.index, autopct='%1.1f%%')
            ax2.set_title('Category Distribution')

            # Line chart: Expenses over time
            daily_expenses = self.filtered_df.groupby('Date')['Amount'].sum()
            ax3.plot(daily_expenses.index, daily_expenses.values)
            ax3.set_title('Daily Expenses')
            ax3.set_ylabel('Amount ($)')
            ax3.tick_params(axis='x', rotation=45)

            # Bar chart: Monthly expenses
            monthly_expenses = self.filtered_df.groupby(self.filtered_df['Date'].dt.to_period('M'))['Amount'].sum()
            ax4.bar(monthly_expenses.index.astype(str), monthly_expenses.values)
            ax4.set_title('Monthly Expenses')
            ax4.set_ylabel('Amount ($)')
            ax4.tick_params(axis='x', rotation=45)

            plt.tight_layout()

            # Embed in Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.chart_canvas)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            # Clear canvas
            for widget in self.chart_canvas.winfo_children():
                widget.destroy()

    def update_data_view(self):
        # Clear existing data
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)

        if self.filtered_df is not None and not self.filtered_df.empty:
            # Set up columns
            columns = list(self.filtered_df.columns)
            self.data_tree['columns'] = columns
            self.data_tree.heading('#0', text='Index')
            for col in columns:
                self.data_tree.heading(col, text=col)
                self.data_tree.column(col, width=100)

            # Insert data
            for idx, row in self.filtered_df.iterrows():
                values = [row[col] for col in columns]
                self.data_tree.insert('', tk.END, text=str(idx), values=values)

    def add_expense(self):
        # Add expense dialog with multiple entry capability
        add_window = tk.Toplevel(self.root)
        add_window.title("Add Expenses")
        add_window.geometry("500x500")

        # Input fields
        input_frame = ttk.Frame(add_window)
        input_frame.pack(pady=10)

        ttk.Label(input_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, pady=2)
        date_entry = ttk.Entry(input_frame)
        date_entry.grid(row=0, column=1, pady=2)

        ttk.Label(input_frame, text="Category:").grid(row=1, column=0, sticky=tk.W, pady=2)
        category_entry = ttk.Entry(input_frame)
        category_entry.grid(row=1, column=1, pady=2)

        ttk.Label(input_frame, text="Amount:").grid(row=2, column=0, sticky=tk.W, pady=2)
        amount_entry = ttk.Entry(input_frame)
        amount_entry.grid(row=2, column=1, pady=2)

        ttk.Label(input_frame, text="Description:").grid(row=3, column=0, sticky=tk.W, pady=2)
        desc_entry = ttk.Entry(input_frame)
        desc_entry.grid(row=3, column=1, pady=2)

        # List of added expenses
        list_frame = ttk.Frame(add_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Label(list_frame, text="Added Expenses:").pack(anchor=tk.W)
        listbox = tk.Listbox(list_frame, height=10)
        listbox.pack(fill=tk.BOTH, expand=True)

        # Total label
        total_label = ttk.Label(list_frame, text="Total: $0.00", font=("Arial", 12, "bold"))
        total_label.pack(anchor=tk.W, pady=5)

        expenses_list = []

        def add_to_list():
            try:
                date = pd.to_datetime(date_entry.get())
                category = category_entry.get()
                amount = float(amount_entry.get())
                desc = desc_entry.get()

                expense = {
                    'Date': date,
                    'Category': category,
                    'Amount': amount,
                    'Description': desc
                }
                expenses_list.append(expense)
                listbox.insert(tk.END, f"{date.strftime('%Y-%m-%d')} - {category} - ${amount:.2f} - {desc}")

                # Clear entries
                date_entry.delete(0, tk.END)
                category_entry.delete(0, tk.END)
                amount_entry.delete(0, tk.END)
                desc_entry.delete(0, tk.END)

                # Update total
                total = sum(e['Amount'] for e in expenses_list)
                total_label.config(text=f"Total: ${total:.2f}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add to list: {str(e)}")

        def save_all():
            if not expenses_list:
                messagebox.showwarning("Warning", "No expenses to save.")
                return

            try:
                new_rows = pd.DataFrame(expenses_list)

                if self.df is None:
                    self.df = new_rows
                else:
                    self.df = pd.concat([self.df, new_rows], ignore_index=True)

                self.clean_data()
                self.apply_filter()
                add_window.destroy()
                messagebox.showinfo("Success", f"{len(expenses_list)} expenses added successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save expenses: {str(e)}")

        def remove_selected():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                del expenses_list[index]
                listbox.delete(index)
                total = sum(e['Amount'] for e in expenses_list)
                total_label.config(text=f"Total: ${total:.2f}")

        # Buttons
        button_frame = ttk.Frame(add_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Add to List", command=add_to_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Selected", command=remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save All", command=save_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=add_window.destroy).pack(side=tk.LEFT, padx=5)

    def set_budget(self, category, entry):
        try:
            budget = float(entry.get())
            if budget <= 0:
                messagebox.showerror("Error", "Budget must be greater than zero.")
                return
            self.budgets[category] = budget
            self.update_dashboard()
            messagebox.showinfo("Success", f"Budget set for {category}: ${budget:.2f}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for budget.")

    def update_dashboard(self):
        if self.filtered_df is not None and not self.filtered_df.empty:
            total = self.filtered_df['Amount'].sum()
            self.total_label.config(text=f"Total Expenses: ${total:.2f}")

            # Check budget status
            overspent = []
            for category, budget in self.budgets.items():
                cat_expenses = self.filtered_df[self.filtered_df['Category'] == category]['Amount'].sum()
                if cat_expenses > budget:
                    overspent.append(category)

            if overspent:
                self.budget_status_label.config(text=f"Overspent in: {', '.join(overspent)}", foreground="red")
            else:
                self.budget_status_label.config(text="Budget Status: On Track", foreground="green")

            # Update progress bars
            for widget in self.progress_bars_container.winfo_children():
                widget.destroy()

            for category in self.category_colors.keys():
                if category in self.budgets:
                    cat_expenses = self.filtered_df[self.filtered_df['Category'] == category]['Amount'].sum()
                    budget = self.budgets[category]
                    if budget <= 0:
                        continue

                    percentage = min(cat_expenses / budget * 100, 100)

                    bar_frame = ttk.Frame(self.progress_bars_container)
                    bar_frame.pack(fill=tk.X, pady=2)
                    ttk.Label(bar_frame, text=f"{category}: ${cat_expenses:.2f}/{budget:.2f}").pack(side=tk.LEFT)
                    progress = ttk.Progressbar(bar_frame, length=200, mode='determinate', value=percentage)
                    progress.pack(side=tk.RIGHT)
                    if percentage > 100:
                        progress.config(style="Red.Horizontal.TProgressbar")
        else:
            self.total_label.config(text="Total Expenses: $0.00")
            self.budget_status_label.config(text="Budget Status: No Data", foreground="black")

            # Clear progress bars
            for widget in self.progress_bars_container.winfo_children():
                widget.destroy()

    def export_csv(self):
        if self.filtered_df is not None and not self.filtered_df.empty:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if file_path:
                try:
                    self.filtered_df.to_csv(file_path, index=False)
                    messagebox.showinfo("Success", "Data exported to CSV successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")
        else:
            messagebox.showerror("Error", "No data to export.")

    def export_pdf(self):
        if self.filtered_df is not None and not self.filtered_df.empty:
            file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
            if file_path:
                try:
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)

                    # Title
                    pdf.cell(200, 10, text="Expense Tracker Report", ln=True, align='C')

                    # Summary
                    total = self.filtered_df['Amount'].sum()
                    pdf.cell(200, 10, text=f"Total Expenses: ${total:.2f}", ln=True)

                    # Category summary
                    pdf.cell(200, 10, text="Expenses by Category:", ln=True)
                    category_sum = self.filtered_df.groupby('Category')['Amount'].sum()
                    for category, amount in category_sum.items():
                        pdf.cell(200, 10, text=f"{category}: ${amount:.2f}", ln=True)

                    pdf.output(file_path)
                    messagebox.showinfo("Success", "Report exported to PDF successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to export PDF: {str(e)}")
        else:
            messagebox.showerror("Error", "No data to export.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()
