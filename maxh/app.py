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

def get_calenders_holidays(maxi,maxj,holidays):
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

    calendars = []
    for year in highlights_dict.keys():
        highlights_list = highlights_dict[year]
        for i in range(1,len(highlights_list)):
            if len(highlights_list[i]):
                if year in leaves_dict:
                    leaves_list = leaves_dict[year]
                    leaves = leaves_list[i]
                else:
                    leaves = []
                c = HighlightedCalendar(highlight=highlights_list[i],
                                leaves=leaves).formatmonth(
                                    year, i)
                calendars.append(c)
    
    highlights_dict.clear()
    leaves_dict.clear()


    return maxholidays, calendars


def bestTimeInAMonth(yy, mm, k):
    today = date.today()
    if today.month == mm and today.year == yy:
        i = j = today
    else:
        i = j = date(yy, mm, 1)

    k = min(k, 366)

    maxj = maxi = date(yy, mm, 1)

    holidays = {}
    cookie_holidays = request.cookies.get('holidays')
    if cookie_holidays is None:
        holidays['All-Saturdays'] = " "
        holidays['All-Sundays'] = " "
    else:
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
    return get_calenders_holidays(maxi,maxj,holidays)


def topChoices(heap, holidays):
    choices = CHOICES  # top m choices
    contextList = []
    heapq.heapify(heap)
    while choices:
        h, maxi, maxj = heapq.heappop(heap)
        maxj -= timedelta(days=1)
        contextList.append(get_calenders_holidays(maxi,maxj,holidays))
        choices -=1
    return contextList


def bestTimeInYear(yy, k):
    yearList = []
    k = min(k, 366)
    today = date.today()
    today += timedelta(days=1)
    mm, dd = today.month, today.day
    i = date(yy, mm, dd)
    j = date(yy, mm, dd)
    holidays = {}
    cookie_holidays = request.cookies.get('holidays')
    if cookie_holidays is None:
        holidays['All-Saturdays'] = " "
        holidays['All-Sundays'] = " "
    else:
        holidays = json.loads(cookie_holidays)
    while j.year <= yy:
        if not isholi(j,holidays):
            k -= 1
        if k < 0:
            yearList.append((-(j - i).days, i, j))
            while i <= j and isholi(i,holidays):
                i += timedelta(days=1)
            k += 1
            i += timedelta(days=1)
        yearList.append((-(j - i).days, i, j))
        
        j += timedelta(days=1)
    yearList.append((-(j - i).days, i, j))
    return topChoices(yearList, holidays)


@app.route('/', methods=['GET', 'POST'])
def home():
    # Render the page
    if request.method == "POST":
        yy = int(request.form.get('yy'))
        mm = int(request.form.get('mm'))
        k = int(request.form.get('k'))
        if 'mmm' in request.form:
            maxholidays, calendars = bestTimeInAMonth(yy, mm, k)
            #print(bestTimeInYear(yy, k))
            return render_template(
            'view.html',
            noHolidays=len(maxholidays),
            k=k,
            month=calendar.month_name[mm],
            holidays=maxholidays,
            calendars=calendars,
            last=maxholidays[len(maxholidays) - 1][0],
        )
        else:
            yearList = bestTimeInYear(yy, k)
            return render_template(
            'yearView.html',
            yearList = yearList,
            k=k,
            choices=CHOICES,
            year=yy,
            )
        
    resp = make_response(render_template('index.html'))
    if 'holidays' not in request.cookies:
        country = get_country(get_ip())
        if country is None:
            country = DEFAULT_COUNTRY_CODE 
        init_holidays = {}
        current_year = date.today().year
        init_holidays = get_holidays(country,current_year)
        if country == DEFAULT_COUNTRY_CODE:
            init_holidays |= allHolidays
            init_holidays = dict(sorted(init_holidays.items()))
        resp.set_cookie('holidays', json.dumps(init_holidays))
    return resp

def get_holidays(country,current_year):
    country_holidays = {}
    country_holidays['All-Saturdays'] = " "
    country_holidays['All-Sundays'] = " "
    try:
        national_holidays = hm.country_holidays(country,years=[current_year,current_year+1])
        for day,name in national_holidays.items():
            country_holidays[str(day)] = name
        if country != DEFAULT_COUNTRY_CODE:
            country_holidays = dict(sorted(country_holidays.items()))
    except Exception as e:
        print(e)
    
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
    if holidays is None:
        return redirect(url_for('.home'))
    if request.method == "POST":
        holidays = request.cookies.get('holidays')
        dictHoliday = json.loads(holidays)
        try:
            if 'mul' in request.form:
                key, val = request.form.get('week'), ' '
                key = key.strip()
                dictHoliday[key] = val
            else:
                key, val = request.form.get('pick'), request.form.get('val')
                key, val = key.strip(), val.strip()
                dictHoliday[key] = val
                dictHoliday = dict(sorted(dictHoliday.items()))
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
CHOICES = 10

if __name__ == '__main__':
    # Run the app server on localhost:5000
    app.run()
