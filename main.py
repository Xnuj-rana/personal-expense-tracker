
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import json
import os
from datetime import date, datetime

APP_TITLE = "Personal Expense Tracker"
DATA_FILE = "expenses.csv"
BUDGET_FILE = "budget.json"

CATEGORIES = [
    "Food", "Transport", "Education", "Shopping",
    "Entertainment", "Health", "Bills", "Other"
]

FIELDS = ["id", "date", "name", "category", "amount", "description"]


class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1050x720")
        self.root.minsize(850, 600)

        self.expenses = []
        self.next_id = 1
        self.monthly_budget = 5000.0

        self.load_expenses()
        self.load_budget()
        self.setup_style()
        self.create_widgets()
        self.refresh_table()

    def setup_style(self):
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Arial", 20, "bold"))
        style.configure("Total.TLabel", font=("Arial", 12, "bold"))
        style.configure("Treeview", rowheight=27)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def create_widgets(self):
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main, text="Personal Expense Tracker",
            style="Title.TLabel"
        ).pack(anchor="w", pady=(0, 12))

        summary = ttk.Frame(main)
        summary.pack(fill="x", pady=(0, 12))

        self.total_label = ttk.Label(
            summary, text="Total Spending: Rs. 0.00",
            style="Total.TLabel"
        )
        self.total_label.pack(side="left", padx=(0, 25))

        self.budget_label = ttk.Label(
            summary, text="Monthly Budget: Rs. 5000.00"
        )
        self.budget_label.pack(side="left", padx=(0, 25))

        self.remaining_label = ttk.Label(
            summary, text="Remaining: Rs. 5000.00"
        )
        self.remaining_label.pack(side="left")

        form = ttk.LabelFrame(main, text="Add New Expense", padding=10)
        form.pack(fill="x", pady=(0, 12))

        ttk.Label(form, text="Expense Name").grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        self.name_entry = ttk.Entry(form, width=25)
        self.name_entry.grid(row=1, column=0, padx=5, pady=4, sticky="ew")

        ttk.Label(form, text="Amount (Rs.)").grid(
            row=0, column=1, sticky="w", padx=5, pady=4
        )
        self.amount_entry = ttk.Entry(form, width=15)
        self.amount_entry.grid(row=1, column=1, padx=5, pady=4, sticky="ew")

        ttk.Label(form, text="Category").grid(
            row=0, column=2, sticky="w", padx=5, pady=4
        )
        self.category_box = ttk.Combobox(
            form, values=CATEGORIES, state="readonly", width=18
        )
        self.category_box.set("Food")
        self.category_box.grid(
            row=1, column=2, padx=5, pady=4, sticky="ew"
        )

        ttk.Label(form, text="Date (YYYY-MM-DD)").grid(
            row=0, column=3, sticky="w", padx=5, pady=4
        )
        self.date_entry = ttk.Entry(form, width=15)
        self.date_entry.insert(0, date.today().isoformat())
        self.date_entry.grid(row=1, column=3, padx=5, pady=4, sticky="ew")

        ttk.Label(form, text="Description (optional)").grid(
            row=2, column=0, sticky="w", padx=5, pady=4
        )
        self.description_entry = ttk.Entry(form, width=40)
        self.description_entry.grid(
            row=3, column=0, columnspan=3,
            padx=5, pady=4, sticky="ew"
        )

        ttk.Button(
            form, text="Add Expense", command=self.add_expense
        ).grid(row=3, column=3, padx=5, pady=4, sticky="ew")

        for column in range(4):
            form.columnconfigure(column, weight=1)

        tools = ttk.Frame(main)
        tools.pack(fill="x", pady=(0, 10))

        ttk.Label(tools, text="Search:").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(tools, width=22)
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.refresh_table)

        ttk.Label(tools, text="Category:").pack(side="left", padx=(0, 5))
        self.filter_box = ttk.Combobox(
            tools, values=["All"] + CATEGORIES,
            state="readonly", width=16
        )
        self.filter_box.set("All")
        self.filter_box.pack(side="left", padx=(0, 10))
        self.filter_box.bind("<<ComboboxSelected>>", self.refresh_table)

        ttk.Button(
            tools, text="Set Monthly Budget",
            command=self.set_budget
        ).pack(side="left", padx=3)

        table_frame = ttk.Frame(main)
        table_frame.pack(fill="both", expand=True)

        columns = ("date", "name", "category", "amount", "description")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            selectmode="extended"
        )

        headings = {
            "date": ("Date", 105),
            "name": ("Expense Name", 170),
            "category": ("Category", 125),
            "amount": ("Amount (Rs.)", 115),
            "description": ("Description", 250)
        }

        for col, (heading, width) in headings.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, minwidth=70)

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        buttons = ttk.Frame(main)
        buttons.pack(fill="x", pady=(10, 0))

        ttk.Button(
            buttons, text="Delete Selected",
            command=self.delete_expense
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            buttons, text="Category Summary",
            command=self.show_summary
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Export CSV",
            command=self.export_csv
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Show All",
            command=self.clear_filters
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons, text="Exit",
            command=self.root.destroy
        ).pack(side="right")

        self.status_label = ttk.Label(
            main, text="Your expenses are saved automatically."
        )
        self.status_label.pack(anchor="w", pady=(8, 0))

    def add_expense(self):
        name = self.name_entry.get().strip()
        amount_text = self.amount_entry.get().strip()
        category = self.category_box.get()
        date_text = self.date_entry.get().strip()
        description = self.description_entry.get().strip()

        if not name:
            messagebox.showerror("Invalid Input", "Enter an expense name.")
            return

        try:
            amount = float(amount_text)
            if not amount > 0 or not amount < float("inf"):
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Input", "Enter a valid positive amount."
            )
            return

        try:
            datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Invalid Date", "Use the date format YYYY-MM-DD."
            )
            return

        expense = {
            "id": str(self.next_id),
            "date": date_text,
            "name": name,
            "category": category,
            "amount": f"{amount:.2f}",
            "description": description
        }

        self.next_id += 1
        self.expenses.append(expense)
        self.save_expenses()
        self.refresh_table()

        self.name_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, date.today().isoformat())
        self.name_entry.focus_set()

        self.status_label.config(text="Expense added successfully!")

    def refresh_table(self, event=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.search_entry.get().strip().lower()
        category_filter = self.filter_box.get()

        for expense in sorted(
            self.expenses,
            key=lambda item: (item["date"], int(item["id"])),
            reverse=True
        ):
            if category_filter != "All" and expense["category"] != category_filter:
                continue

            searchable = " ".join(
                expense[field] for field in
                ("date", "name", "category", "description")
            ).lower()

            if search and search not in searchable:
                continue

            self.tree.insert(
                "", "end", iid=expense["id"],
                values=(
                    expense["date"],
                    expense["name"],
                    expense["category"],
                    f'{float(expense["amount"]):.2f}',
                    expense["description"]
                )
            )

        self.update_summary()

    def update_summary(self):
        current_month = date.today().strftime("%Y-%m")

        monthly_total = sum(
            float(expense["amount"])
            for expense in self.expenses
            if expense["date"].startswith(current_month)
        )

        all_total = sum(float(e["amount"]) for e in self.expenses)
        remaining = self.monthly_budget - monthly_total

        self.total_label.config(
            text=f"Total Spending: Rs. {all_total:.2f}"
        )
        self.budget_label.config(
            text=f"This Month: Rs. {monthly_total:.2f} / "
                 f"Rs. {self.monthly_budget:.2f}"
        )
        self.remaining_label.config(
            text=f"Remaining: Rs. {remaining:.2f}"
        )

        if remaining < 0:
            self.remaining_label.config(foreground="red")
        else:
            self.remaining_label.config(foreground="green")

    def delete_expense(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Selection", "Select one or more expenses to delete."
            )
            return

        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete {len(selected)} selected expense(s)?"
        ):
            return

        selected_ids = set(selected)
        self.expenses = [
            expense for expense in self.expenses
            if expense["id"] not in selected_ids
        ]

        self.save_expenses()
        self.refresh_table()
        self.status_label.config(text="Selected expenses deleted.")

    def set_budget(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Set Monthly Budget")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(
            dialog, text="Enter monthly budget (Rs.):"
        ).pack(padx=20, pady=(20, 5))

        entry = ttk.Entry(dialog)
        entry.pack(padx=20, pady=5)
        entry.insert(0, str(self.monthly_budget))
        entry.focus_set()

        def save_budget():
            try:
                amount = float(entry.get().strip())
                if not amount > 0 or not amount < float("inf"):
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid Budget",
                    "Enter a valid positive budget.",
                    parent=dialog
                )
                return

            self.monthly_budget = amount
            self.save_budget_file()
            self.update_summary()
            dialog.destroy()

        ttk.Button(
            dialog, text="Save Budget", command=save_budget
        ).pack(pady=(8, 20))

        entry.bind("<Return>", lambda event: save_budget())

    def show_summary(self):
        totals = {}

        for expense in self.expenses:
            category = expense["category"]
            totals[category] = (
                totals.get(category, 0) + float(expense["amount"])
            )

        window = tk.Toplevel(self.root)
        window.title("Category Summary")
        window.geometry("380x400")

        ttk.Label(
            window, text="Spending by Category",
            style="Title.TLabel"
        ).pack(pady=15)

        if not totals:
            ttk.Label(window, text="No expenses recorded yet.").pack(pady=10)
            return

        for category, amount in sorted(
            totals.items(), key=lambda item: item[1], reverse=True
        ):
            ttk.Label(
                window,
                text=f"{category}: Rs. {amount:.2f}",
                font=("Arial", 11)
            ).pack(anchor="w", padx=25, pady=5)

        total = sum(totals.values())
        ttk.Separator(window).pack(fill="x", padx=20, pady=10)
        ttk.Label(
            window, text=f"Grand Total: Rs. {total:.2f}",
            style="Total.TLabel"
        ).pack(pady=5)

    def clear_filters(self):
        self.search_entry.delete(0, tk.END)
        self.filter_box.set("All")
        self.refresh_table()

    def load_expenses(self):
        if not os.path.exists(DATA_FILE):
            return

        try:
            with open(DATA_FILE, "r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    try:
                        amount = float(row["amount"])
                        if not amount > 0 or not amount < float("inf"):
                            continue

                        datetime.strptime(row["date"], "%Y-%m-%d")

                        expense_id = row.get("id", "").strip()
                        if not expense_id or any(
                            e["id"] == expense_id for e in self.expenses
                        ):
                            expense_id = str(self.next_id)

                        self.expenses.append({
                            "id": expense_id,
                            "date": row["date"],
                            "name": row["name"],
                            "category": row["category"],
                            "amount": f"{amount:.2f}",
                            "description": row.get("description", "")
                        })

                        self.next_id = max(
                            self.next_id, int(expense_id) + 1
                        )
                    except (ValueError, KeyError, TypeError):
                        continue

        except (OSError, csv.Error) as error:
            messagebox.showerror(
                "File Error", f"Could not load expenses:\n{error}"
            )

    def save_expenses(self):
        try:
            with open(DATA_FILE, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(self.expenses)
        except (OSError, csv.Error) as error:
            messagebox.showerror(
                "Save Error", f"Could not save expenses:\n{error}"
            )

    def load_budget(self):
        if not os.path.exists(BUDGET_FILE):
            return

        try:
            with open(BUDGET_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                amount = float(data["monthly_budget"])

                if amount > 0 and amount < float("inf"):
                    self.monthly_budget = amount
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            self.monthly_budget = 5000.0

    def save_budget_file(self):
        try:
            with open(BUDGET_FILE, "w", encoding="utf-8") as file:
                json.dump(
                    {"monthly_budget": self.monthly_budget},
                    file, indent=4
                )
        except OSError as error:
            messagebox.showerror(
                "Save Error", f"Could not save budget:\n{error}"
            )

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Export Expenses",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="my_expenses.csv"
        )

        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(self.expenses)

            messagebox.showinfo(
                "Export Successful", f"Expenses exported to:\n{path}"
            )
        except (OSError, csv.Error) as error:
            messagebox.showerror(
                "Export Error", f"Could not export expenses:\n{error}"
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
