"""
URL configuration for library project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve
from application import views
from application.views import student_profile

urlpatterns = [
    path('', views.index, name='index'),
    path('admin-signup/', views.admin_signup, name='admin-signup'),
    path('student-signup/', views.student_signup, name='student-signup'),
    path('admin-login/', views.admin_login, name='admin-login'),
    path('student-login/', views.student_login, name='student-login'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student-dashboard'),
    path('add-book', views.add_book, name='add-book'),
    path('manage-books/', views.manage_books, name='manage-books'),
    path('update-book/<int:book_id>/', views.update_book, name='update-book'),
    path('delete-book/<int:book_id>/', views.delete_book, name='delete-book'),
    path('admin-messages/', views.admin_messages, name='admin-messages'),
    path('admin/students/', views.admin_students, name='admin-students'),
    path('admin/edit-student/<int:student_id>/', views.edit_student, name='edit-student'),
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow-book'),
    path('my-books/', views.student_borrowed_books, name='student-borrowed-books'),
    path('student-logout/', views.student_logout, name='student-logout'),
    path("student-profile/", views.student_profile, name="student-profile"),
    path('admin/borrowed-books/', views.admin_borrowed_books, name='admin-borrowed-books'),
    path('return/<int:borrow_id>/', views.return_book, name='return-book'),

]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
