import tkinter as tk

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sidebar Navigation Example")
        self.geometry("700x450")

        self.sidebar = tk.Frame(self, width=180, bg="#121824")
        self.sidebar.pack(fill="y", side="left")
        self.sidebar.pack_propagate(False) # Prevents sidebar from shrinking

        self.main_container = tk.Frame(self, bg="#1A2333")
        self.main_container.pack(fill="both", expand=True, side="right")

        self.frames = {}

        for PageClass in (DiscountCalc, TempConverter, RectangleCalc, AVGGradeCalc, TimeConverter, SalaryCalc, BMICalc, CircleCalc, LoanCalc, ShoppingCartCalc):
            page_name = PageClass.__name__
            frame = PageClass(parent=self.main_container, controller=self)
            self.frames[page_name] = frame
            # Grid all frames on top of each other in the same space
            frame.grid(row=0, column=0, sticky="nsew")

        # Configure container grid weights so frames fill the space
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.create_nav_button("Discount Calc", "DiscountCalc")
        self.create_nav_button("Temp Converter", "TempConverter")
        self.create_nav_button("Rectangle Calc", "RectangleCalc")
        self.create_nav_button("AVG Grade Calc", "AVGGradeCalc")
        self.create_nav_button("Time Converter", "TimeConverter")
        self.create_nav_button("Salary Calc", "SalaryCalc")
        self.create_nav_button("BMI Calc", "BMICalc")
        self.create_nav_button("Circle Calc", "CircleCalc")
        self.create_nav_button("Loan Calc", "LoanCalc")
        self.create_nav_button("Shopping Cart Calc", "ShoppingCartCalc")

        self.show_frame("DiscountCalc")

    def create_nav_button(self, text, page_name):
        btn = tk.Button(
            self.sidebar, 
            text=text, 
            bg="#34495e", 
            fg="white", 
            activebackground="#2D3748",
            relief="flat",
            command=lambda: self.show_frame(page_name)
        )
        btn.pack(fill="x", padx=10, pady=5, ipady=5)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

class DiscountCalc(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1A2333")
        label = tk.Label(self, text="Discount Calculator", font=("Arial", 18), bg="#1A2333")
        label.pack(pady=40, padx=40)

class TempConverter(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1A2333")
        label = tk.Label(self, text="Temperature Converter", font=("Arial", 18), bg="#1A2333")
        label.pack(pady=40, padx=40)

class RectangleCalc(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1A2333")
        label = tk.Label(self, text="Rectangle Calculator", font=("Arial", 18), bg="#1A2333")
        label.pack(pady=40, padx=40)

class AVGGradeCalc(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1A2333")
        label = tk.Label(self, text="Average Grade Calculator", font=("Arial", 18), bg="#1A2333")
        label.pack(pady=40, padx=40)

class TimeConverter(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1A2333")
        label = tk.Label(self, text="Time Converter", font=("Arial", 18), bg="#1A2333")
        label.pack(pady=40, padx=40)

class SalaryCalc(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1A2333")
        label = tk.Label(self, text="Salary Calculator", font=("Arial", 18), bg="#1A2333")
        label.pack(pady=40, padx=40)

class BMICalc(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1A2333")
        label = tk.Label(self, text="BMI Calculator", font=("Arial", 18), bg="#1A2333")
        label.pack(pady=40, padx=40)

class CircleCalc(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1A2333")
        label = tk.Label(self, text="Circle Calculator", font=("Arial", 18), bg="#1A2333")
        label.pack(pady=40, padx=40)

class LoanCalc(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1A2333")
        label = tk.Label(self, text="Loan Calculator", font=("Arial", 18), bg="#1A2333")
        label.pack(pady=40, padx=40) 

class ShoppingCartCalc(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1A2333")
        label = tk.Label(self, text="Shopping Cart Calculator", font=("Arial", 18), bg="#1A2333")
        label.pack(pady=40, padx=40) 

if __name__ == "__main__":
    app = App()
    app.mainloop()
