from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Sum
import csv
from datetime import timedelta
from .models import Expense
from .forms import ExpenseForm
from .forms import ExpenseForm

@login_required
def dashboard(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date', '-id')
    
    filter_type = request.GET.get('filter')
    today = timezone.now().date()
    
    if filter_type == 'today':
        expenses = expenses.filter(date=today)
    elif filter_type == 'week':
        start_week = today - timedelta(days=today.weekday())
        expenses = expenses.filter(date__gte=start_week)
    elif filter_type == 'month':
        expenses = expenses.filter(date__year=today.year, date__month=today.month)
        
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="expenses_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Description', 'Category', 'Amount', 'Notes'])
        for exp in expenses:
            writer.writerow([exp.date, exp.description, exp.category, exp.amount, exp.notes])
        return response

    category_data = list(expenses.values('category').annotate(total=Sum('amount')).order_by('-total'))
    date_data = list(expenses.values('date').annotate(total=Sum('amount')).order_by('date'))

    context = {
        'expenses': expenses,
        'filter_type': filter_type,
        'category_data': category_data,
        'date_data': date_data,
    }
    return render(request, 'expenses/dashboard.html', context)

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            
            if expense.category == 'Other':
                description_lower = expense.description.lower()
                keyword_map = {
                    'uber': 'Travel', 'taxi': 'Travel', 'flight': 'Travel',
                    'pizza': 'Food', 'burger': 'Food', 'restaurant': 'Food', 'zomato': 'Food', 'swiggy': 'Food',
                    'doctor': 'Health', 'pharmacy': 'Health', 'hospital': 'Health',
                    'electricity': 'Utilities', 'water': 'Utilities', 'internet': 'Utilities', 'wifi': 'Utilities',
                    'movie': 'Entertainment', 'netflix': 'Entertainment', 'cinema': 'Entertainment',
                    'amazon': 'Shopping', 'cloth': 'Shopping', 'supermarket': 'Shopping'
                }
                for kw, cat in keyword_map.items():
                    if kw in description_lower:
                        expense.category = cat
                        break
            
            expense.user = request.user
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'expenses/add_expense.html', {'form': form})

@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('dashboard')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'expenses/edit_expense.html', {'form': form, 'expense': expense})

@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('dashboard')
    return render(request, 'expenses/delete_expense.html', {'expense': expense})
