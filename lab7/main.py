def read_int(prompt):
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("Invalid input. Please enter an integer.")


def read_float(prompt):
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("Invalid input. Please enter a number.")


def even_or_odd():
    print("\nTask 1. Even or Odd Number")
    number = read_int("Enter an integer: ")

    if number % 2 == 0:
        print(f"{number} is even.")
    else:
        print(f"{number} is odd.")


def exam_admission():
    print("\nTask 2. Exam Admission")
    attendance = read_float("Enter attendance percentage: ")
    project_done = input("Has the project been completed? (y/n): ").strip().lower()

    if attendance >= 70 and project_done in ("yes", "y"):
        print("Allowed to exam")
    else:
        print("Not allowed")


def grade_calculator():
    print("\nTask 3. Student Grade Calculator")
    score = read_float("Enter final score (0-100): ")

    if score < 0 or score > 100:
        print("Error: score must be between 0 and 100.")
        return

    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 50:
        grade = "C"
    else:
        grade = "F"

    print(f"Score: {score:g}")
    print(f"Grade: {grade}")


def discount_calculator():
    print("\nTask 4. Discount Calculator")
    amount = read_float("Enter purchase amount (KZT): ")

    if amount < 0:
        print("Error: purchase amount cannot be negative.")
        return

    if amount < 10000:
        discount_percent = 0
    elif amount < 50000:
        discount_percent = 5
    elif amount < 100000:
        discount_percent = 10
    else:
        discount_percent = 15

    discount_amount = amount * discount_percent / 100
    final_amount = amount - discount_amount

    print(f"\nOriginal amount:\t{amount:.2f} KZT")
    print(f"Discount:\t\t{discount_percent}%")
    print(f"Final amount:\t\t{final_amount:.2f} KZT")


def day_of_week():
    print("\nTask 5. Day of the Week")
    day_number = read_int("Enter a number from 1 to 7: ")

    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    if 1 <= day_number <= 7:
        print(days[day_number - 1])
    else:
        print("Invalid day number")


def numbers_from_one_to_n():
    print("\nTask 6. Numbers from 1 to N")
    n = read_int("Enter a positive integer N: ")

    if n < 1:
        print("Error: N must be a positive integer.")
        return

    numbers = [str(i) for i in range(1, n + 1)]
    print(", ".join(numbers))


def sum_of_numbers():
    print("\nTask 7. Sum of Numbers")
    n = read_int("Enter a positive integer N: ")

    if n < 1:
        print("Error: N must be a positive integer.")
        return

    total = 0
    i = 1
    while i <= n:
        total += i
        i += 1

    print(f"Sum of numbers from 1 to {n}: {total}")


def multiplication_table():
    print("\nTask 8. Multiplication Table")
    number = read_int("Enter an integer: ")

    for i in range(1, 11):
        print(f"{number} × {i} = {number * i}")


def password_verification():
    print("\nTask 9. Password Verification")

    while True:
        password = input("Enter password: ").strip()
        if password == "java123":
            print("Access granted")
            break
        print("Incorrect password. Try again.")


def atm_simulator():
    print("\nTask 10. ATM Simulator")
    balance = 100000.0

    while True:
        print("\nATM Menu")
        print(" 1. Check balance")
        print(" 2. Deposit money")
        print(" 3. Withdraw money")
        print(" 4. Exit")

        choice = read_int("Select an option (1-4): ")

        if choice == 1:
            print(f"Current balance: {balance:.2f} KZT")
        elif choice == 2:
            amount = read_float("Enter deposit amount (KZT): ")
            if amount <= 0:
                print("Error: deposit must be greater than zero.")
            else:
                balance += amount
                print(f"Deposit successful. New balance: {balance:.2f} KZT")
        elif choice == 3:
            amount = read_float("Enter withdrawal amount (KZT): ")
            if amount <= 0:
                print("Error: withdrawal must be greater than zero.")
            elif amount > balance:
                print("Error: insufficient funds.")
            else:
                balance -= amount
                print(f"Withdrawal successful. New balance: {balance:.2f} KZT")
        elif choice == 4:
            print("Thank you for using the ATM. Goodbye!")
            break
        else:
            print("Error: invalid menu choice.")


def show_menu():
    print("\nweb lab7")
    print(" 1. Even or Odd Number")
    print(" 2. Exam Admission")
    print(" 3. Student Grade Calculator")
    print(" 4. Discount Calculator")
    print(" 5. Day of the Week")
    print(" 6. Numbers from 1 to N")
    print(" 7. Sum of Numbers")
    print(" 8. Multiplication Table")
    print(" 9. Password Verification")
    print("10. ATM Simulator")
    print(" 0. Exit")


def main():
    tasks = {
        1: even_or_odd,
        2: exam_admission,
        3: grade_calculator,
        4: discount_calculator,
        5: day_of_week,
        6: numbers_from_one_to_n,
        7: sum_of_numbers,
        8: multiplication_table,
        9: password_verification,
        10: atm_simulator,
    }

    while True:
        show_menu()
        choice = input("Select a task (0-10): ").strip()

        if choice == "0":
            break

        if choice.isdigit() and int(choice) in tasks:
            tasks[int(choice)]()
        else:
            print("\nInvalid input")


if __name__ == "__main__":
    main()
