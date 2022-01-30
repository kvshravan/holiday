from flask import Flask, request, render_template
import calendar
from datetime import date, timedelta
import heapq
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
    if day.weekday() == 6 or day.weekday() == 5:
        return 1
    if str(day) in holidays:
        return 2
    return 0


def bestTimeInAMonth(yy, mm, k, s):
    s += (calendar.HTMLCalendar().formatmonth(yy, mm))
    noDays = calendar.monthrange(yy, mm)[1]
    i = j = 1
    ans = 0
    storage = [0]*(noDays+1)
    maxj, maxi = 0, 0
    while j <= noDays:
        day = date(yy, mm, j)
        storage[j] = isholi(day)
        if not storage[j]:
            k -= 1
        if k < 0:
            if j-i > maxj-maxi:
                ans = max(ans, j-i)
                maxi = i
                maxj = j
            while i <= j and storage[i]:
                i += 1
            k += 1
            i += 1
        if j-i > maxj-maxi:
            ans = max(ans, j-i)
            maxi = i
            maxj = j
        j += 1
    if j-i > maxj-maxi:
        ans = max(ans, j-i)
        maxi = i
        maxj = j
    s += "<br>Maximum holidays - <b>"+str(ans) + "</b> <br>"
    for i in range(maxi, maxj):
        day = date(yy, mm, i)
        s += "<br>"
        var = storage[i]
        if not var:
            s = s + "<b>" + str(day) + " - Leave</b>"
        else:
            if var == 1:
                s = s + str(day) + " - Holiday (Weekend)"
            else:
                s = s + str(day) + " - Holiday" + \
                            "(" + holidays[str(day)] + ")"
    return s


def topChoices(stack, storage, s):
    while stack:
        h, maxi, maxj = heapq.heappop(stack)
        s += "<br>Maximum holidays - <b>" + str(h) + "</b> <br>"
        s += "<h4>from " + str(maxi)
        s += " to " + str(maxj)+"<br></h4>"
        for i in range(maxi.month, maxj.month+1):
            s += (calendar.HTMLCalendar().formatmonth(maxi.year, i))
            s += "<br>"
        print(maxi, maxj)
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
        return s


def bestTimeInYear(yy, k, s):
    stack = []
    m = 20  # top m choices
    storage = [[0 for i in range(1, 33)] for j in range(1, 14)]
    heapq.heapify(stack)
    today = date.today()
    mm, dd = today.month, today.day
    i = date(yy, mm, dd)
    j = date(yy, mm, dd)
    while j.year <= yy:
        storage[j.month][j.day] = isholi(j)
        if not storage[j.month][j.day]:
            k -= 1
        if k < 0:
            if len(stack) < m:
                heapq.heappush(stack, ((j-i).days, i, j))
            elif (j-i).days > stack[0][0]:
                heapq.heappop(stack)
                heapq.heappush(stack, ((j-i).days, i, j))
            while i <= j and storage[i.month][i.day]:
                i += timedelta(days=1)
            k += 1
            i += timedelta(days=1)
        if len(stack) < m:
            heapq.heappush(stack, ((j-i).days, i, j))
        elif (j-i).days > stack[0][0]:
            heapq.heappop(stack)
            heapq.heappush(stack, ((j-i).days, i, j))
        j += timedelta(days=1)
    if len(stack) < m:
        heapq.heappush(stack, ((j-i).days, i, j))
    elif (j-i).days > stack[0][0]:
        heapq.heappop(stack)
        heapq.heappush(stack, ((j-i).days, i, j))
    return topChoices(stack, storage, s)


@app.route('/', methods=['GET', 'POST'])
def hello():
    # Render the page
    if request.method == "POST":
        print(request.form)
        yy = int(request.form.get('yy'))
        mm = int(request.form.get('mm'))
        k = int(request.form.get('k'))
        print(calendar.month(yy, mm))
        s = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        if 'mmm' in request.form:
            s = bestTimeInAMonth(yy, mm, k, s)
        else:
            s = bestTimeInYear(yy, k, s)
        return s
    return render_template("form.html")


holidays = {
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
}

if __name__ == '__main__':
    # Run the app server on localhost:5000
    app.run('localhost', 5000, debug=True)
