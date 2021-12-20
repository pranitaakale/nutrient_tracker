from django.shortcuts import render
import pymssql
import environ

env = environ.Env()
environ.Env.read_env()


def index(request):
    # return render(request, 'tracker/index.html')
    conn = pymssql.connect(
        server=env('DB_HOST'), user=env('DB_USER'), password=env('DB_PASSWORD'), database=env('DB_NAME'))

    cursor = conn.cursor()

    cursor.execute("SELECT * from UserDetails")
    get_users = cursor.fetchall()
    conn.commit
    return render(request, 'tracker/index.html', {'get_users': get_users})

    # if request.method == 'POST':
    #     userid = request.POST['userid']
    #     messages.success(request, {userid})
    #     request.session['userid'] = userid
    #     conn.commit
    #     return redirect('homepage')

    # else:
    #     cursor.execute("SELECT * from UserDetails")
    #     get_users = cursor.fetchall()
    #     conn.commit
    #     return render(request, 'userdetails/loginform.html', {'get_users': get_users})
