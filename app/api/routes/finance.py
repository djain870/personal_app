from datetime import datetime
from collections import defaultdict

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import extract

from app.core.templates import templates
from app.db.session import SessionLocal
from app.models import Cashflow, Expense, Wealth
from app.utils.auth import get_current_user

router = APIRouter()


#finance management routes
@router.get("/finances")
def finance(request: Request, month: str = None, view: str = "table"):
    db = SessionLocal()
    user = get_current_user(request)

    year = None
    month_filter = None
    
    # -------- Default KPI values (avoid UnboundLocalError) --------
    latest_value = 0
    change = 0
    change_pct = 0

    # -------- Cashflow defaults --------
    income = {}
    expense_cf = {}
    savings = {}
    latest_income = 0
    latest_expense = 0
    latest_savings = 0
    savings_rate = 0
    
    if not user:
        return RedirectResponse(url="/login")
    if month:
        try:
            year, month_num = map(int, month.split("-"))
        except:
            return RedirectResponse("/finances")

        expenses = db.query(Expense).filter(
            extract("year", Expense.date) == year,
            extract("month", Expense.date) == month_num,
            Expense.user == user
        ).all()
    else:
        expenses = db.query(Expense).filter(Expense.user == user).all()
    total = sum(e.amount for e in expenses)
    category_totals = defaultdict(float)
    for e in expenses:
        category_totals[e.category] += e.amount  

    # -------- Wealth dashboard logic --------
    networth = {}
    type_totals = {}
    volatility_totals = {}

    if view == "wealth":
        year = request.query_params.get("year")
        month_filter = request.query_params.get("month")

        # -------- Get all available dates (for defaults + filters) --------
        all_dates = db.query(Wealth.month).filter(Wealth.user == user).all()
        unique_dates = sorted(set([d[0] for d in all_dates if d[0]]))

        # -------- Default to latest year/month if not provided --------
        if unique_dates:
            latest_date = max(unique_dates)

            if not year:
                year = str(latest_date.year)

            if not month_filter:
                month_filter = latest_date.strftime("%Y-%m")

        # -------- Base Query (user + year filter) --------
        wealth_query = db.query(Wealth).filter(Wealth.user == user)

        if year:
            try:
                wealth_query = wealth_query.filter(
                    extract("year", Wealth.month) == int(year)
                )
            except:
                pass

        wealth_data = wealth_query.all()

        networth_dict = defaultdict(float)

        # -------- Networth (YEAR FILTER APPLIES) --------
        for w in wealth_data:
            key = w.month.strftime("%Y-%m")
            networth_dict[key] += w.balance

        networth = dict(networth_dict)

        # -------- KPI Calculations --------
        prev_value = 0

        if networth:
            sorted_months = sorted(networth.keys())
            latest_month_key = sorted_months[-1]
            latest_value = networth[latest_month_key]

            if len(sorted_months) > 1:
                prev_month_key = sorted_months[-2]
                prev_value = networth[prev_month_key]
                change = latest_value - prev_value
                if prev_value != 0:
                    change_pct = (change / prev_value) * 100

        # -------- Asset Allocation (MONTH FILTER APPLIES) --------
        type_dict = defaultdict(float)

        allocation_data = wealth_data

        if month_filter:
            try:
                y, m = map(int, month_filter.split("-"))
                allocation_data = [
                    w for w in wealth_data
                    if w.month.year == y and w.month.month == m
                ]
            except:
                allocation_data = wealth_data
        else:
            # default → latest month within filtered data
            if wealth_data:
                latest_month = max(w.month for w in wealth_data)
                allocation_data = [
                    w for w in wealth_data if w.month == latest_month
                ]

        for w in allocation_data:
            type_dict[w.type] += w.balance

        type_totals = dict(type_dict)

        # -------- Volatility Split (MONTH FILTER APPLIES like allocation) --------
        volatility_dict = defaultdict(float)

        for w in allocation_data:
            volatility_dict[w.volatility] += w.balance

        volatility_totals = dict(volatility_dict)

    # -------- Cashflow dashboard logic --------
    if view == "cashflow":
        year = request.query_params.get("year")
        month_filter = request.query_params.get("month")

        # get available dates for defaults
        all_dates_cf = db.query(Cashflow.month).filter(Cashflow.user == user).all()
        unique_dates_cf = sorted(set([d[0] for d in all_dates_cf if d[0]]))

        if unique_dates_cf:
            latest_date_cf = max(unique_dates_cf)
            if not year:
                year = str(latest_date_cf.year)
            if not month_filter:
                month_filter = latest_date_cf.strftime("%Y-%m")

        cf_query = db.query(Cashflow).filter(Cashflow.user == user)

        if year:
            try:
                cf_query = cf_query.filter(
                    extract("year", Cashflow.month) == int(year)
                )
            except:
                pass

        cf_data = cf_query.all()

        income_dict = defaultdict(float)
        expense_dict = defaultdict(float)
        savings_dict = defaultdict(float)

        for c in cf_data:
            key = c.month.strftime("%Y-%m")
            if c.flag == "Income":
                income_dict[key] += c.amount
            elif c.flag == "Expense":
                expense_dict[key] += c.amount
            elif c.flag == "Savings":
                savings_dict[key] += c.amount

        income = dict(income_dict)
        expense_cf = dict(expense_dict)
        savings = dict(savings_dict)

        # KPIs (latest month)
        if income:
            sorted_months = sorted(income.keys())
            latest_key = sorted_months[-1]

            latest_income = income.get(latest_key, 0)
            latest_expense = expense_cf.get(latest_key, 0)
            latest_savings = savings.get(latest_key, 0)

            if latest_income != 0:
                savings_rate = (latest_savings / latest_income) * 100

    # -------- Dynamic Year & Month Filters --------
    years = []
    months = []

    if view == "wealth":
        years = sorted(set([d.year for d in unique_dates]))
        months = [d.strftime("%Y-%m") for d in unique_dates]
    elif view == "cashflow":
        years = sorted(set([d.year for d in unique_dates_cf])) if 'unique_dates_cf' in locals() else []
        months = [d.strftime("%Y-%m") for d in unique_dates_cf] if 'unique_dates_cf' in locals() else []

    db.close()
    return templates.TemplateResponse(
        "finances.html",
        {
            "request": request,
            "expenses": expenses,
            "total": total,
            "category_totals": dict(category_totals),
            "view": view,
            "networth": networth,
            "type_totals": type_totals,
            "volatility_totals": volatility_totals,
            "years": years,
            "months": months,
            "year": year,
            "month_filter": month_filter,
            "latest_value": latest_value,
            "change": change,
            "change_pct": change_pct,
            "income": income,
            "expense_cf": expense_cf,
            "savings": savings,
            "latest_income": latest_income,
            "latest_expense": latest_expense,
            "latest_savings": latest_savings,
            "savings_rate": savings_rate
        }
    )

  

@router.post("/finances/add")
def add_expense(
    request: Request,
    amount: float = Form(...),
    category: str = Form(...),
    note: str = Form(""),
    date: str = Form(...)
):
    db = SessionLocal()
    user = get_current_user(request)

    parsed_date = datetime.strptime(date, "%Y-%m-%d").date()

    expense = Expense(
        amount=amount,
        category=category,
        note=note,
        date=parsed_date,
        user=user
    )

    db.add(expense)
    db.commit()
    db.close()

    return RedirectResponse(url="/finances", status_code=303)


@router.get("/finances/delete/{id}")
def delete_expense(request: Request, id: int):
    db = SessionLocal()
    user = get_current_user(request)
    expense = db.query(Expense).filter(
        Expense.id == id,
        Expense.user == user
    ).first()

    if not expense:
        db.close()
        return RedirectResponse("/finances")

    db.delete(expense)
    db.commit()
    db.close()

    return RedirectResponse(url="/finances/", status_code=303)


@router.get("/finances/edit/{id}")
def edit_page(request: Request, id: int):
    db = SessionLocal()
    user = get_current_user(request)
    expense = db.query(Expense).filter(
        Expense.id == id,
        Expense.user == user
    ).first()
    db.close()

    return templates.TemplateResponse(
        "finances_edit.html",
        {"request": request, "expense": expense}
    )


@router.post("/finances/update/{id}")
def update_expense(
    request: Request,
    id: int,
    amount: float = Form(...),
    category: str = Form(...),
    note: str = Form(""),
    date: str = Form(...)
):
    db = SessionLocal()
    user = get_current_user(request)
    expense = db.query(Expense).filter(
        Expense.id == id,
        Expense.user == user
    ).first()

    expense.amount = amount
    expense.category = category
    expense.note = note
    parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
    expense.date = parsed_date

    db.commit()
    db.close()

    return RedirectResponse(url="/finances", status_code=303)
