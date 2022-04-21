from ipaddress import ip_address
from re import L
from unittest.mock import DEFAULT
import requests
from flask import Flask, request, render_template, make_response, redirect, url_for
import calendar
from datetime import date, timedelta
import heapq
import json
import holidays as hm
# Create an instance of the Flask class that is the WSGI application.
# The first argument is the name of the application module or package,
# typically __name__ when using a single module.
app = Flask(__name__)

# Flask route decorators map / and /hello to the hello function.
# To add other resources, create functions that generate the page contents
# and add decorators to define the appropriate resource locators for them.


class HighlightedCalendar(calendar.HTMLCalendar):

    def __init__(self, highlight=[], leaves=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._highlight = highlight
        self._leaves = leaves

    def formatday(self, day, weekday):
        """
        Return a day as a table cell.
        """
        if day in self._leaves:
            return '<td class="%s" style="font-weight: 750;color:red;" bgcolor="pink">%d</td>' % (
                self.cssclasses[weekday], day)
        elif self._highlight[0] <= day <= self._highlight[1]:
            return '<td class="%s" style="font-weight: 750;" bgcolor="pink">%d</td>' % (
                self.cssclasses[weekday], day)
        else:
            if day == 0:
                # day outside month
                return '<td class="%s" style="font-weight: 750;">&nbsp;</td>' % self.cssclass_noday
            else:
                return '<td class="%s" style="font-weight: 750;">%d</td>' % (
                    self.cssclasses[weekday], day)

    def formatmonth(self, theyear, themonth, withyear=True):
        """
        Return a formatted month as a table.
        """
        v = []
        a = v.append
        a('<table border="0" cellpadding="2" cellspacing="0" class="%s">' %
          (self.cssclass_month))
        a('\n')
        a(self.formatmonthname(theyear, themonth, withyear=withyear))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


def isholi(day, holidays):
    days = (0,1,2,3,4,5,6)
    dictKeys = ("All-Mondays","All-Tuesdays","All-Wednesdays","All-Thursdays","All-Fridays","All-Saturdays","All-Sundays")
    for i in days:
        if day.weekday() == i and dictKeys[i] in holidays:
            return 1
    if str(day) in holidays:
        return 2
    return 0


def bestTimeInAMonth(yy, mm, k, s):
    today = date.today()
    if today.month == mm:
        i = j = today
    else:
        i = j = date(yy, mm, 1)

    k = min(k, 366)

    maxj = maxi = date(yy, mm, 1)

    cookie_holidays = request.cookies.get('holidays')
    holidays = json.loads(cookie_holidays)

    while i.month <= mm and i.year <= yy:
        if not isholi(j, holidays):
            k -= 1
        if k < 0:
            if (j - i).days > (maxj - maxi).days:
                maxi = i
                maxj = j
            while i.month <= mm and i <= j and isholi(i, holidays):
                i += timedelta(days=1)
            k += 1
            i += timedelta(days=1)
        if (j - i).days > (maxj - maxi).days:
            maxi = i
            maxj = j
        j += timedelta(days=1)

    if (j - i).days > (maxj - maxi).days:
        maxi = i
        maxj = j

    maxj -= timedelta(days=1)

    maxholidays = []
    highlights_dict = {}
    leaves_dict = {}

    while maxi <= maxj:
        day = maxi
        d = day.strftime("%d %B, %Y")

        if maxi.year not in highlights_dict:
            highlights_dict[maxi.year] = [[] for i in range(13)]
        highlights_list = highlights_dict[maxi.year]

        if len(highlights_list[maxi.month]):
            highlights_list[maxi.month][1] = maxi.day
        else:
            highlights_list[maxi.month].append(maxi.day)
            highlights_list[maxi.month].append(maxi.day)

        var = isholi(maxi,holidays)
        if not var:
            maxholidays.append((d, 0))
            if maxi.year not in leaves_dict:
                leaves_dict[maxi.year] = [[] for i in range(13)]
            leaves_list = leaves_dict[maxi.year]
            leaves_list[maxi.month].append(maxi.day)
        elif var == 1:
            maxholidays.append((d, 1))
        else:
            maxholidays.append((d, holidays[str(day)]))

        maxi += timedelta(days=1)

    
    print(highlights_dict)
    print(leaves_dict)

    calendars = []

    for year in highlights_dict.keys():
        highlights_list = highlights_dict[year]
        for i in range(1,len(highlights_list)):
            if len(highlights_list[i]):
                leaves_list = leaves_dict[year]
                c = HighlightedCalendar(highlight=highlights_list[i],
                                leaves=leaves_list[i]).formatmonth(
                                    year, i)
                calendars.append(c)
    
    highlights_dict.clear()
    leaves_dict.clear()


    return maxholidays, calendars


def topChoices(heap, storage, s):
    m = 20  # top m choices
    holidays = request.cookies.get('holidays')
    cookie_holidays = request.cookies.get('holidays')
    holidays = json.loads(cookie_holidays)
    while m:
        h, maxi, maxj = heapq.heappop(heap)
        h *= -1
        s += "<br>Maximum holidays - <b>" + str(h) + "</b> <br>"
        s += "<h4>from " + maxi.strftime("%d %B, %Y")
        s += " to " + maxj.strftime("%d %B, %Y") + "<br></h4>"
        maxmonth = maxj.month + 1
        if maxj.year > maxi.year:
            maxmonth = 13
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
    k = min(k, 366)
    s += "<br> Here are the best 20 choices picked for you with atmost " + \
        str(k) + " leaves starting from tomorrow :) <br>"
    storage = [[0 for i in range(1, 33)] for j in range(1, 14)]
    heapq.heapify(stack)
    today = date.today()
    today += timedelta(days=1)
    mm, dd = today.month, today.day
    i = date(yy, mm, dd)
    j = date(yy, mm, dd)
    while j.year <= yy:
        storage[j.month][j.day] = isholi(j)
        if not storage[j.month][j.day]:
            k -= 1
        if k < 0:
            heapq.heappush(stack, (-(j - i).days, i, j))
            while i <= j and storage[i.month][i.day]:
                i += timedelta(days=1)
            k += 1
            i += timedelta(days=1)
        heapq.heappush(stack, (-(j - i).days, i, j))
        j += timedelta(days=1)
    heapq.heappush(stack, (-(j - i).days, i, j))
    return topChoices(stack, storage, s)


@app.route('/', methods=['GET', 'POST'])
def home():
    # Render the page
    c = get_country(get_ip())
    print(c)
    highlight = range(1, 7)
    if request.method == "POST":
        yy = int(request.form.get('yy'))
        mm = int(request.form.get('mm'))
        k = int(request.form.get('k'))
        s = ''
        if 'mmm' in request.form:
            maxholidays, calendars = bestTimeInAMonth(yy, mm, k, s)
        else:
            s = bestTimeInYear(yy, k, s)
        return render_template(
            'view.html',
            noHolidays=len(maxholidays),
            k=k,
            month=calendar.month_name[mm],
            holidays=maxholidays,
            calendars=calendars,
            last=maxholidays[len(maxholidays) - 1][0],
        )
    resp = make_response(render_template('index.html'))
    if 'holidays' not in request.cookies:
        country = get_country(get_ip())
        if country is None:
            country = DEFAULT_COUNTRY_CODE 
    
        current_year = date.today().year
        init_holidays = get_holidays(country,current_year)
        resp.set_cookie('holidays', json.dumps(init_holidays))
    return resp

def get_holidays(country,current_year):
    national_holidays = hm.country_holidays(country,years=[current_year,current_year+1])
    country_holidays = {}
    for day,name in national_holidays.items():
        country_holidays[str(day)] = name
    country_holidays['All-Saturdays'] = " "
    country_holidays['All-Sundays'] = " "
    return country_holidays


def get_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']


def get_country(ip):
    try:
        response = requests.get("http://ip-api.com/json/{}".format(ip))
        js = response.json()
        country = js['countryCode']
        return country
    except Exception as e:
        print(e)
        print('failed to get country name')


@app.route('/holiday', methods=['GET', 'POST'])
def holiday():
    holidays = request.cookies.get('holidays')
    if request.method == "POST":
        holidays = request.cookies.get('holidays')
        dictHoliday = json.loads(holidays)
        try:
            if 'mul' in request.form:
                key, val = request.form.get('week'), ' '
                print(request.form)
                key = key.strip()
            else:
                key, val = request.form.get('pick'), request.form.get('val')
                key, val = key.strip(), val.strip()
            dictHoliday[key] = val
            resp = make_response(
                redirect(url_for('.holiday', _external=True, _scheme="https")))
            resp.set_cookie('holidays', json.dumps(dictHoliday))
            return resp
        except Exception as e:
            print(e)
    return render_template('hview.html', days=json.loads(holidays))


@app.route('/remove/<key>', methods=['GET', 'POST'])
def removeHoliday(key):
    holidays = request.cookies.get('holidays')
    if holidays is not None:
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


@app.route('/about', methods=['GET'])
def about():
    print('Hello')
    us_h = hm.country_holidays('IN',years=[2022,2023])
    for day in us_h.items():
        print(day)
    return render_template('about.html')


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
    "2022-10-02": "Mahatma Gandhi's Birthday",
    "2022-10-03": "Durga Puja",
    "2022-10-04": "Navami",
    "2022-10-05": "Dussehra",
    "2022-10-09": "Id-e-Milad",
    "2022-10-24": "Deepavali",
    "2022-11-08": "Guru Nanak's Birthday",
    "2022-12-25": "Christmas",
    "All-Saturdays": " ",
    "All-Sundays": " "
}
DEFAULT_COUNTRY_CODE = 'IN'

if __name__ == '__main__':
    # Run the app server on localhost:5000
    app.run(debug=True)
