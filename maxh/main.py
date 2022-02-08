from flask import Flask, request, render_template, make_response, redirect, url_for
import calendar
from datetime import date, timedelta
import heapq
import json
# Create an instance of the Flask class that is the WSGI application.
# The first argument is the name of the application module or package,
# typically __name__ when using a single module.
app = Flask(__name__)

# Flask route decorators map / and /hello to the hello function.
# To add other resources, create functions that generate the page contents
# and add decorators to define the appropriate resource locators for them.


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


def isholi(day):
    holidays = request.cookies.get('holidays')
    if holidays is None:
        holidays = allHolidays
    else:
        holidays = json.loads(holidays)
    if day.weekday() == 6 and "All-Sundays" in holidays:
        return 1
    if day.weekday() == 5 and "All-Saturdays" in holidays:
        return 1
    if str(day) in holidays:
        return 2
    return 0


def bestTimeInAMonth(yy, mm, k, s):
    i = j = date(yy, mm, 1)
    ans = 0
    s += "<br> Here is the best pick for you with atmost " + \
        str(k) + " leaves in the month of " + \
        calendar.month_name[mm]+":) <br><br>"
    storage = [[0 for i in range(1, 33)] for j in range(1, 14)]
    maxj = maxi = date(yy, mm, 1)
    while i.month <= mm:
        storage[j.month][j.day] = isholi(j)
        if not storage[j.month][j.day]:
            k -= 1
        if k < 0:
            if (j-i).days > (maxj-maxi).days:
                maxi = i
                maxj = j
            while i.month <= mm and i <= j and storage[i.month][i.day]:
                i += timedelta(days=1)
            k += 1
            i += timedelta(days=1)
        if (j-i).days > (maxj-maxi).days:
            maxi = i
            maxj = j
        j += timedelta(days=1)
    if (j-i).days > (maxj-maxi).days:
        maxi = i
        maxj = j
    ans = (maxj-maxi).days
    maxmonth = maxj.month+1
    holidays = request.cookies.get('holidays')
    if holidays is None:
        holidays = allHolidays
    else:
        holidays = json.loads(holidays)
    if maxj.year > maxi.year:
        maxmonth = 12
    for i in range(maxi.month, maxmonth):
        s += (calendar.HTMLCalendar().formatmonth(maxi.year, i))
        s += "<br>"
    s += "<br>Maximum holidays - <b>"+str(ans) + "</b> <br>"
    while maxi < maxj:
        day = maxi
        d = day.strftime("%d %B, %Y")
        s += "<br>"
        var = storage[maxi.month][maxi.day]
        if not var:
            s = s + "<b>" + d + " - Leave</b>"
        else:
            if var == 1:
                s = s + d + " - Holiday (Weekend)"
            else:
                s = s + d + " - Holiday" + \
                            "(" + holidays[str(day)] + ")"
        maxi += timedelta(days=1)
    s += "<br>-----------------------------------------------------------------------------<br>"
    return s


def topChoices(heap, storage, s):
    m = 20  # top m choices
    holidays = request.cookies.get('holidays')
    if holidays is None:
        holidays = allHolidays
    else:
        holidays = json.loads(holidays)
    while m:
        h, maxi, maxj = heapq.heappop(heap)
        h *= -1
        s += "<br>Maximum holidays - <b>" + str(h) + "</b> <br>"
        s += "<h4>from " + maxi.strftime("%d %B, %Y")
        s += " to " + maxj.strftime("%d %B, %Y")+"<br></h4>"
        maxmonth = maxj.month+1
        if maxj.year > maxi.year:
            maxmonth = 12
        for i in range(maxi.month, maxmonth):
            s += (calendar.HTMLCalendar().formatmonth(maxi.year, i))
            s += "<br>"
        while maxi < maxj:
            day = maxi
            s += "<br>"
            var = storage[maxi.month][maxi.day]
            if not var:
                s = s + "<b>" + str(day) + " - Leave</b>"
            else:
                if var == 1:
                    s = s + str(day) + " - Holiday (Weekend)"
                else:
                    s = s + str(day) + " - Holiday" + \
                                "(" + holidays[str(day)] + ")"
            maxi += timedelta(days=1)
        s += "<br>-----------------------------------------------------------------------------<br>"
        m -= 1
    return s


def bestTimeInYear(yy, k, s):
    stack = []
    s += "<br> Here are the best 20 choices picked for you with atmost " + \
        str(k) + " leaves starting from tomorrow :) <br>"
    storage = [[0 for i in range(1, 33)] for j in range(1, 14)]
    heapq.heapify(stack)
    today = date.today()
    today += timedelta(days=1)
    print(today.day)
    mm, dd = today.month, today.day
    i = date(yy, mm, dd)
    j = date(yy, mm, dd)
    print(i)
    while j.year <= yy:
        storage[j.month][j.day] = isholi(j)
        if not storage[j.month][j.day]:
            k -= 1
        if k < 0:
            heapq.heappush(stack, (-(j-i).days, i, j))
            while i <= j and storage[i.month][i.day]:
                i += timedelta(days=1)
            k += 1
            i += timedelta(days=1)
        heapq.heappush(stack, (-(j-i).days, i, j))
        j += timedelta(days=1)
    heapq.heappush(stack, (-(j-i).days, i, j))
    return topChoices(stack, storage, s)


@app.route('/', methods=['GET', 'POST'])
def hello():
    # Render the page
    print('Home')
    if request.method == "POST":
        yy = int(request.form.get('yy'))
        mm = int(request.form.get('mm'))
        k = int(request.form.get('k'))
        s = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        if 'mmm' in request.form:
            s = bestTimeInAMonth(yy, mm, k, s)
        else:
            s = bestTimeInYear(yy, k, s)
        return s
    resp = make_response(render_template('form.html'))
    if 'holidays' not in request.cookies:
        resp.set_cookie('holidays', json.dumps(allHolidays))
    return resp


@app.route('/holiday', methods=['GET', 'POST'])
def holiday():
    holidays = request.cookies.get('holidays')
    print(holidays)
    if request.method == "POST":
        holidays = request.cookies.get('holidays')
        dictHoliday = json.loads(holidays)
        print(request.form)
        try:
            key, val = request.form.get('pick'), request.form.get('val')
            key, val = key.strip(), val.strip()
            dictHoliday[key] = val
            resp = make_response(
                redirect(url_for('.holiday', _external=True, _scheme="https")))
            resp.set_cookie('holidays', json.dumps(dictHoliday))
            return resp
        except Exception as e:
            print(e)
    return render_template('holiday.html', days=json.loads(holidays))


@app.route('/remove/<key>', methods=['GET', 'POST'])
def removeHoliday(key):
    holidays = request.cookies.get('holidays')
    dictHoliday = json.loads(holidays)
    try:
        del dictHoliday[key]
        resp = make_response(
            redirect(url_for('holiday', _external=True, _scheme="https")))
        resp.set_cookie('holidays', json.dumps(dictHoliday))
        return resp
    except Exception as e:
        print(e)
    return redirect(url_for('holiday'))


allHolidays = {
    "2022-01-13": "Uruka /Lohri",
    "2022-01-14": "Shankranti",
    "2022-01-26": "Republic Day",
    "2022-03-18": "Holi",
    "2022-04-14": "Mahavir Jayanti",
    "2022-04-15": "Good Friday",
    "2022-05-03": "Id-ul-Fitr",
    "2022-05-16": "Buddha Purnima",
    "2022-07-10": "Id-ul-Zuha",
    "2022-08-09": "Muharram",
    "2022-08-15": "Independence Day",
    "2022-10-02": "Mahatma Gandhi’s Birthday",
    "2022-10-03": "Durga Puja ",
    "2022-10-04": "Durga Puja (Navami)",
    "2022-10-05": "Dussehra",
    "2022-10-09": "Id-e-Milad",
    "2022-10-24": "Deepavali",
    "2022-11-08": "Guru Nanak’s Birthday",
    "2022-12-25": "Christmas",
    "All-Saturdays": " ",
    "All-Sundays": " "
}

if __name__ == '__main__':
    # Run the app server on localhost:5000
    app.run()
