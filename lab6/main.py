import math


def discount_calculator():
    print("\nDiscount Calculator")
    price = float(input("Enter product price: "))
    if price <= 0:
        print("Invalid input")
        return
    
    quantity = int(input("Enter quantity: "))
    if quantity <= 0:
        print("Invalid input")
        return
    
    discount_percent = float(input("Enter discount percentage: "))
    if discount_percent <= 0:
        print("Invalid input")
        return

    subtotal = price * quantity
    discount_amount = subtotal * (discount_percent / 100)
    final_price = subtotal - discount_amount

    print(f"\nSubtotal before discount:\t{subtotal:.2f}")
    print(f"Discount amount:\t\t{discount_amount:.2f}")
    print(f"Final price after discount:\t{final_price:.2f}")


def temperature_converter():
    print("\nTemperature Converter")
    celsius = float(input("Enter temperature in Celsius: "))
    if celsius <= 0:
        print("Invalid input")
        return

    fahrenheit = (celsius * 9 / 5) + 32
    print(f"\n{celsius:.2f} °C = {fahrenheit:.2f} °F")


def rectangle_calculator():
    print("\nRectangle Calculator")
    width = float(input("Enter rectangle width: "))
    if width <= 0:
        print("Invalid input")
        return
    
    height = float(input("Enter rectangle height: "))
    if height <= 0:
        print("Invalid input")
        return

    area = width * height
    perimeter = 2 * (width + height)

    print(f"\nArea:      {area:.2f}")
    print(f"Perimeter: {perimeter:.2f}")


def average_grade_calculator():
    print("\nAverage Grade Calculator")
    grade1 = float(input("Enter grade 1: "))
    if grade1 < 0 or grade1 > 100:
        print("Invalid grade. Grade must be between 0 and 100.")
        return
    grade2 = float(input("Enter grade 2: "))
    if grade2 < 0 or grade2 > 100:
        print("Invalid grade. Grade must be between 0 and 100.")
        return
    grade3 = float(input("Enter grade 3: "))
    if grade3 < 0 or grade3 > 100:
        print("Invalid grade. Grade must be between 0 and 100.")
        return

    average = (grade1 + grade2 + grade3) / 3
    print(f"\nAverage grade: {average:.2f}")


def time_converter():
    print("\nTime Converter")
    total_minutes = int(input("Enter total number of minutes: "))
    if total_minutes <= 0:
        print("Invalid input")
        return

    hours = total_minutes // 60
    minutes = total_minutes % 60

    print(f"\n{total_minutes} minutes = {hours} hours {minutes} minutes")


def salary_calculator():
    print("\nSalary Calculator")
    name = input("Enter employee name: ")

    hours_worked = float(input("Enter number of hours worked: "))
    if hours_worked <= 0:
        print("Invalid input")
        return
    
    hourly_rate = float(input("Enter hourly rate: "))
    if hourly_rate <= 0:
        print("Invalid input")
        return

    tax_rate = 0.10
    gross_salary = hours_worked * hourly_rate
    tax_amount = gross_salary * tax_rate
    net_salary = gross_salary - tax_amount

    print(f"\nEmployee name: {name}")
    print(f"Gross salary:\t{gross_salary:.2f}")
    print(f"Tax amount:\t{tax_amount:.2f}")
    print(f"Net salary:\t{net_salary:.2f}")


def bmi_calculator():
    print("\nBMI Calculator")
    weight = float(input("Enter weight in kg: "))
    if weight <= 0:
        print("Invalid input")
        return

    height = float(input("Enter height in cm: ")) / 100
    if height <= 0:
        print("Invalid input")
        return
    
    bmi = weight / (height ** 2)
    print(f"\nBMI: {bmi:.2f}")


def circle_calculator():
    print("\nCircle Calculator")
    radius = float(input("Enter the radius of the circle: "))
    if radius <= 0:
        print("Invalid input")
        return

    area = math.pi * radius ** 2
    circumference = 2 * math.pi * radius

    print(f"\nArea:\t{area:.2f}")
    print(f"Circumference:\t{circumference:.2f}")


def loan_calculator():
    print("\nLoan Calculator")
    loan_amount = float(input("Enter loan amount: "))
    if loan_amount <= 0:
        print("Invalid input")
        return
    
    annual_rate = float(input("Enter annual interest rate (%): "))
    if annual_rate <= 0:
        print("Invalid input")
        return
    
    years = float(input("Enter loan term in years: "))
    if years <= 0:
        print("Invalid input")
        return

    total_interest = loan_amount * (annual_rate / 100) * years
    total_repayment = loan_amount + total_interest
    months = years * 12
    monthly_payment = total_repayment / months if months > 0 else 0

    print(f"\nTotal interest amount:\t{total_interest:.2f}")
    print(f"Total repayment amount:\t{total_repayment:.2f}")
    print(f"Approximate monthly payment:\t{monthly_payment:.2f}")


def shopping_cart_calculator():
    print("\nShopping Cart Calculator")
    customer_name = input("Enter customer name: ")
    product_name = input("Enter product name: ")

    price_per_item = float(input("Enter price per item: "))
    if price_per_item <= 0:
        print("Invalid input")
        return
    
    quantity = int(input("Enter quantity: "))
    if quantity <= 0:
        print("Invalid input")
        return
    
    discount_percent = float(input("Enter discount percentage: "))
    if discount_percent <= 0:
        print("Invalid input")
        return
    
    delivery_cost = float(input("Enter delivery cost: "))
    if delivery_cost <= 0:
        print("Invalid input")
        return

    subtotal = price_per_item * quantity
    discount_amount = subtotal * (discount_percent / 100)
    final_total = subtotal - discount_amount + delivery_cost

    print(f"Customer name:\t{customer_name}")
    print(f"Product name:\t{product_name}")
    print(f"Quantity:\t{quantity}")
    print(f"Subtotal:\t{subtotal:.2f}")
    print(f"Discount amount:\t{discount_amount:.2f}")
    print(f"Delivery cost:\t{delivery_cost:.2f}")
    print(f"Final total:\t{final_total:.2f}")


def show_menu():
    print("\nweb lab6")
    print(" 1. Discount Calculator")
    print(" 2. Temperature Converter")
    print(" 3. Rectangle Calculator")
    print(" 4. Average Grade Calculator")
    print(" 5. Time Converter")
    print(" 6. Salary Calculator")
    print(" 7. BMI Calculator")
    print(" 8. Circle Calculator")
    print(" 9. Loan Calculator")
    print("10. Shopping Cart Calculator")
    print(" 0. Exit")


def main():
    tasks = {
        1: discount_calculator,
        2: temperature_converter,
        3: rectangle_calculator,
        4: average_grade_calculator,
        5: time_converter,
        6: salary_calculator,
        7: bmi_calculator,
        8: circle_calculator,
        9: loan_calculator,
        10: shopping_cart_calculator,
    }

    while True:
        show_menu()
        choice = input("Select a task (0-10): ").strip()

        if choice == "0":
            break

        if choice.isdigit() and int(choice) in tasks:
            try:
                tasks[int(choice)]()
            except ValueError:
                print("\nInvalid input")
        else:
            print("\nInvalid input")


if __name__ == "__main__":
    main()