from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Student, Contact, Book, Admin, Borrow
from django.contrib.auth.hashers import make_password
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from datetime import date, timedelta
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from functools import wraps

from django.db import transaction
from django.db.models import F


def admin_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_username'):
            messages.error(request, "Please log in as an admin.")
            return redirect('admin-login')
        return view(request, *args, **kwargs)
    return wrapper


def mark_returned(borrow_id, **filters):
    with transaction.atomic():
        borrow = Borrow.objects.select_for_update().filter(id=borrow_id, returned=False, **filters).first()
        if not borrow:
            return None
        borrow.returned = True
        borrow.save()
        Book.objects.filter(id=borrow.book_id).update(available_copies=F('available_copies') + 1)
    return borrow


def student_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        student = Student.objects.filter(username=request.session.get('student_username')).first()
        if not student:
            messages.error(request, "Please log in to continue.")
            return redirect('student-login')
        request.student = student
        return view(request, *args, **kwargs)
    return wrapper



def index(request):
    return render(request, 'index.html')
def about(request):
    return render(request, 'about.html')

def admin_login(request):
    return render(request, 'admin_login.html')

def student_login(request):
    return render(request, 'student_login.html')

@admin_required
def admin_dashboard(request):
# If user is an admin, proceed to gather dashboard data
    total_books = Book.objects.count()
    total_borrowed = Borrow.objects.count()
    total_students = Student.objects.count()

    context = {
        'total_books': total_books,
        'total_borrowed': total_borrowed,
        'total_students': total_students,
    }
    return render(request, 'admin_dashboard.html', context)

def student_signup(request):
    if request.method == "POST":
        username = request.POST['username']
        full_name = request.POST['full_name']
        email = request.POST['email']
        password = request.POST['password']

        # Check if the username already exists in the application_student table
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM application_student WHERE username = %s", [username])
            if cursor.fetchone()[0] > 0:
                messages.error(request, "Username already exists. Please choose a different one.")
                return redirect('student-signup')

        # Hash the password for security
        hashed_password = make_password(password)

        # Save the student details into the `application_student` table
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO application_student (username, full_name, email, password)
                VALUES (%s, %s, %s, %s)
                """,
                [username, full_name,email, hashed_password]
            )

        messages.success(request, "Student account created successfully!")
        return redirect('student-signup')  # Redirect to the student login page

    return render(request, 'student_signup.html')


def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        with connection.cursor() as cursor:
            # Fetch the student's details from the database
            cursor.execute("SELECT * FROM application_student WHERE username=%s", [username])
            student_user = cursor.fetchone()

        if student_user:
            # Assuming the password is stored in the 4th column (adjust the index based on your table structure)
            stored_hashed_password = student_user[4]

            # Verify the entered password against the hashed password
            if check_password(password, stored_hashed_password):
                # Simulate session login for the student
                request.session['student_username'] = username
                messages.success(request, "Welcome to the student dashboard!")
                return redirect("student-dashboard")  # Replace with your actual student dashboard URL
            else:
                messages.error(request, "Invalid credentials, please try again.")
        else:
            messages.error(request, "Invalid credentials, please try again.")

    return render(request, "student_login.html")



def admin_signup(request):
    if Admin.objects.exists() and not request.session.get('admin_username'):
        messages.error(request, "Admin sign-up is closed. Ask an existing admin to create your account.")
        return redirect('admin-login')
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        # Check if the username already exists in the application_admin table
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM application_admin WHERE username = %s", [username])
            if cursor.fetchone()[0] > 0:
                messages.error(request, "Username already exists. Please choose a different one.")
                return redirect('admin-signup')

        # Hash the password for security
        hashed_password = make_password(password)

        # Save the admin details into the `application_admin` table
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO application_admin (username, email, password)
                VALUES (%s, %s, %s)
                """,
                [username, email, hashed_password]
            )

        messages.success(request, "Admin account created successfully!")
        return redirect('admin-signup')  # Redirect to the admin login page

    return render(request, 'admin_signup.html')

def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM application_admin WHERE username=%s", [username])
            admin_user = cursor.fetchone()

        if admin_user:
            # Fetch the hashed password stored in the database
            stored_hashed_password = admin_user[3]  # Assuming password is at index 3 in the tuple

            # Check if the provided password matches the stored hashed password
            if check_password(password, stored_hashed_password):
                # Simulate session login for the admin
                request.session['admin_username'] = username
                messages.success(request, "Welcome to the admin dashboard!")
                return redirect("admin-dashboard")  # Replace with your actual admin dashboard URL
            else:
                messages.error(request, "Invalid credentials, please try again.")
        else:
            messages.error(request, "Invalid credentials, please try again.")

    return render(request, "admin_login.html")

def contact(request):
    if request.method == "POST":
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        # Create and save the contact message to the database
        contact_message = Contact(email=email, phone=phone, message=message)
        contact_message.save()

        messages.success(request, "Your message has been sent successfully.")
        return redirect('contact')  # Redirect to the contact page or a success page

    return render(request, 'contact.html')

@admin_required
def add_book(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        publication_date = request.POST.get('publication_date')
        available_copies = request.POST.get('available_copies')
        cover_image = request.FILES.get('cover_image')

        # Check if all fields are filled
        if title and author and publication_date and available_copies:
            # Save the book to the database
            Book.objects.create(
                title=title,
                author=author,
                publication_date=publication_date,
                cover_image=cover_image,
                available_copies=available_copies
            )
            # Display success message
            messages.success(request, "Book added successfully!")
            return redirect('add-book')  # Redirect to the admin dashboard
        else:
            # Display error message
            messages.error(request, "All fields are required to add a book!")

    return render(request, 'add_books.html')

@admin_required
def manage_books(request):
    # Fetch all books from the database
    books = Book.objects.all()
    return render(request, 'manage_books.html', {'books': books})

@admin_required
def update_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        book.title = request.POST.get('title')
        book.author = request.POST.get('author')
        book.publication_date = request.POST.get('publication_date')
        book.isbn = request.POST.get('isbn')
        book.genre = request.POST.get('genre')
        book.available_copies = request.POST.get('available_copies')

        # If a new image is uploaded
        if request.FILES.get('cover_image'):
            book.cover_image = request.FILES.get('cover_image')

        book.save()
        messages.success(request, 'Book updated successfully!')
        return redirect('manage-books')
    return render(request, 'update_book.html', {'book': book})

@admin_required
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    book.delete()
    messages.success(request, 'Book deleted successfully!')
    return redirect('manage-books')

@admin_required
def admin_messages(request):
    # Fetch all messages from the application_contact table
    messages = Contact.objects.all()

    return render(request, 'admin_messages.html', {'messages': messages})

@admin_required
def admin_students(request):
    # Fetch all students from the application_student table
    students = Student.objects.all()

    return render(request, 'admin_students.html', {'students': students})

@admin_required
def edit_student(request, student_id):
    try:
        student = Student.objects.get(pk=student_id)
    except Student.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('admin-students')

    if request.method == "POST":
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        username = request.POST.get('username')

        # Update student details
        student.full_name = full_name
        student.email = email
        student.username = username
        student.save()

        messages.success(request, "Student details updated successfully.")
        return redirect('admin-students')

    return render(request, 'edit_student.html', {'student': student})

@student_required
def student_dashboard(request):
    # Fetch all available books
    books = Book.objects.all()

    return render(request, 'student_dashboard.html', {'books': books})

@student_required
def borrow_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        try:
            number_of_days = int(request.POST.get('number_of_days', 0))
        except ValueError:
            number_of_days = 0
        if not 1 <= number_of_days <= 30:
            messages.error(request, "Choose between 1 and 30 days.")
            return redirect('borrow-book', book_id=book_id)

        if Borrow.objects.filter(student=request.student, book=book, returned=False).exists():
            messages.error(request, f"You already have '{book.title}'. Return it before borrowing it again.")
            return redirect('student-borrowed-books')

        with transaction.atomic():
            taken = Book.objects.filter(id=book.id, available_copies__gt=0).update(available_copies=F('available_copies') - 1)
            if not taken:
                messages.error(request, f"Sorry, no copies of '{book.title}' are available right now.")
                return redirect('student-dashboard')
            Borrow.objects.create(
                student=request.student,
                book=book,
                start_date=date.today(),
                return_date=date.today() + timedelta(days=number_of_days),
            )
        messages.success(request, f"You borrowed '{book.title}'.")
        return redirect('student-borrowed-books')

    return render(request, 'borrow_book.html', {'book': book})

@student_required
def student_borrowed_books(request):
    student = request.student

    if request.method == "POST":
        borrow = mark_returned(request.POST.get('borrow_id'), student=student)
        if not borrow:
            raise Http404
        messages.success(request, f"'{borrow.book.title}' returned.")
        return redirect('student-borrowed-books')

    borrowed_books = Borrow.objects.filter(student=student, returned=False).select_related('book')
    return render(request, 'student_borrowed_books.html', {'borrowed_books': borrowed_books, 'student': student})

def student_logout(request):
    request.session.flush()
    return redirect('student-login')

@student_required
def student_profile(request):
    student_username = request.session.get("student_username")  # Assuming the username is stored in the session

    if request.method == "POST":
        password = request.POST.get("password")

        if password:
            hashed_password = make_password(password)  # Hash the password
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE application_student SET password=%s WHERE username=%s",
                    [hashed_password, student_username]
                )
            messages.success(request, "Password updated successfully.")
            return redirect("student-dashboard")  # Redirect to the dashboard
        else:
            messages.error(request, "Password cannot be empty.")

    # Fetch student details to display
    with connection.cursor() as cursor:
        cursor.execute("SELECT username, full_name, email FROM application_student WHERE username=%s", [student_username])
        student = cursor.fetchone()

    if not student:
        messages.error(request, "Student not found.")
        return redirect("student-dashboard")

    context = {
        "student": {
            "username": student[0],
            "full_name": student[1],
            "email": student[2],
        }
    }
    return render(request, "student_profile.html", context)


@admin_required
def admin_borrowed_books(request):
    borrowed_books = Borrow.objects.select_related('student', 'book').all()

    return render(request, 'admin_borrowed_books.html', {
        'borrowed_books': borrowed_books,
    })


@admin_required
def return_book(request, borrow_id):
    if request.method == "POST":
        borrow = mark_returned(borrow_id)
        if borrow:
            messages.success(request, f"{borrow.book.title} marked as returned.")
    return redirect("admin-borrowed-books")