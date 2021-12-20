from django.shortcuts import render, redirect, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from datetime import date
from django.views.decorators.csrf import csrf_exempt
import pymssql
import environ

env = environ.Env()
environ.Env.read_env()


def index(request):
    # return render(request, 'tracker/index.html')
    conn = pymssql.connect(
        server=env('DB_HOST'), user=env('DB_USER'), password=env('DB_PASSWORD'), database=env('DB_NAME'))

    cursor = conn.cursor()

    # cursor.execute("SELECT * from UserDetails")
    # get_users = cursor.fetchall()
    # conn.commit
    # return render(request, 'tracker/index.html', {'get_users': get_users})

    if request.method == 'POST':
        userid = request.POST['userid']
        messages.success(request, {userid})
        request.session['userid'] = userid
        conn.commit
        return redirect('homepage')

    else:
        cursor.execute("SELECT * from UserDetails")
        get_users = cursor.fetchall()
        conn.commit
        return render(request, 'tracker/index.html', {'get_users': get_users})


@csrf_exempt
def homepage(request):
    conn = pymssql.connect(
        server=env('DB_HOST'), user=env('DB_USER'), password=env('DB_PASSWORD'), database=env('DB_NAME'))
    cursor = conn.cursor()
    userid = request.session['userid']
    today = date.today()
    mealdate = today.strftime("%Y-%m-%d")

    if 'set-date' in request.POST:
        date_meal = request.POST['date_meal']
    else:
        date_meal = mealdate

    cursor.execute("SELECT * from FoodItems")
    get_food_items = cursor.fetchall()

    cursor.execute("SELECT * FROM UserDetails WHERE ID=%s", userid)
    user_details = cursor.fetchone()

    cursor.execute("SELECT * from FoodItems")
    get_food_items = cursor.fetchall()

    cursor.execute("SELECT Tag FROM FoodItems GROUP BY Tag")
    get_food_tags = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM UserMeals WHERE UserID=%s AND MealDate=%s", (userid, date_meal))
    meal_details = cursor.fetchall()

    cursor.execute(
        "SELECT C_ID FROM UserMeals WHERE UserID=%s AND MealDate=%s", (userid, date_meal))
    meal_ids = cursor.fetchall()

    if meal_ids:

        meal_id_list = []
        for m in meal_ids:
            meal_id_list.append(m[0])
        meal_id_list = tuple(meal_id_list)

        placeholders = ', '.join(['%s']*len(meal_id_list))
        query = 'SELECT * FROM PerMealUserConsumption WHERE Consume_ID IN ({})'.format(
            placeholders)

        cursor.execute(query, meal_id_list)
        get_food_per_meal = cursor.fetchall()

        query2 = 'SELECT Consume_ID,ROUND(SUM(Cal),2), ROUND(SUM(Pro),2), ROUND(SUM(Ft),2), ROUND(SUM(Carb),2) FROM PerMealUserConsumption WHERE Consume_ID IN ({}) GROUP BY Consume_ID'.format(
            placeholders)
        cursor.execute(query2, meal_id_list)
        get_sum_per_meal = cursor.fetchall()

        query3 = 'SELECT ROUND(SUM(Cal),2), ROUND(SUM(Pro),2), ROUND(SUM(Ft),2), ROUND(SUM(Carb),2) FROM PerMealUserConsumption WHERE Consume_ID IN ({}) '.format(
            placeholders)
        cursor.execute(query3, meal_id_list)
        get_sum_per_day = cursor.fetchall()
    else:
        get_food_per_meal = []
        get_sum_per_meal = []
        get_sum_per_day = []

    cursor.execute(
        'SELECT C_ID FROM UserMeals WHERE CONVERT(datetime, MealDate, 11)>= DATEADD(day, -7, GETDATE()) AND UserID=%s', userid)
    get_week = cursor.fetchall()
    if get_week:
        get_week_list = []
        for w in get_week:
            get_week_list.append(w[0])
        get_week_list = tuple(get_week_list)
        placeholders2 = ', '.join(['%s']*len(get_week_list))
        query5 = 'SELECT ROUND(SUM(Cal),2), ROUND(SUM(Pro),2), ROUND(SUM(Ft),2), ROUND(SUM(Carb),2) FROM PerMealUserConsumption WHERE Consume_ID IN ({}) '.format(
            placeholders2)
        cursor.execute(query5, get_week_list)
        get_sum_week = cursor.fetchall()
    else:
        get_sum_week = []

    context = {'user_details': user_details,
               'get_food_items': get_food_items,
               'get_food_tags': get_food_tags,
               'date_meal': date_meal,
               'meal_details': meal_details,
               'get_food_per_meal': get_food_per_meal,
               'get_sum_per_meal': get_sum_per_meal,
               'get_sum_per_day': get_sum_per_day,
               'get_sum_week': get_sum_week}

    if request.method == 'POST':
        if 'add_meal' in request.POST:
            enter_meal = request.POST['enter_meal']
            date_here = request.POST['date_here']
            userid = request.POST['userid']
            cursor.execute(
                "INSERT INTO UserMeals (UserID, Meal, MealDate) VALUES (%s, %s, %s)", (userid, enter_meal, date_here))
            conn.commit()
            return HttpResponseRedirect(reverse('homepage'))

        if 'add_food' in request.POST:
            food_id = request.POST['food_id']
            meal_id = request.POST['meal_id']
            quantity = request.POST['quantit']
            cursor.execute("SELECT * FROM FoodItems WHERE F_ID=%s", food_id)
            food_breakdown = cursor.fetchall()
            food = food_breakdown[0][1]
            cal = float(quantity)*food_breakdown[0][3]
            pro = float(quantity)*food_breakdown[0][4]
            ft = float(quantity)*food_breakdown[0][5]
            carb = float(quantity)*food_breakdown[0][6]

            cursor.execute(
                "INSERT INTO PerMealUserConsumption (Consume_ID, Food_ID, Itemquantity, Cal, Pro, Ft, Carb, Food_name) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (meal_id, food_id, quantity, cal, pro, ft, carb, food))
            conn.commit()
            return HttpResponseRedirect(reverse('homepage'))

        if 'delmeal' in request.POST:
            del_meal_id = request.POST['del-meal']
            cursor.execute("DELETE FROM UserMeals WHERE C_ID=%s", del_meal_id)
            conn.commit()
            return HttpResponseRedirect(reverse('homepage'))

        if 'delfood' in request.POST:
            del_food_id = request.POST['del-food']
            cursor.execute(
                "DELETE FROM PerMealUserConsumption WHERE M_ID=%s", del_food_id)
            conn.commit()
            return HttpResponseRedirect(reverse('homepage'))

        return render(request, 'userdetails/homepage.html', context)

    else:
        return render(request, 'userdetails/homepage.html', context)
