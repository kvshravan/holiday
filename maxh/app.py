import requests
from flask import Flask, request, render_template, make_response, redirect, url_for, abort
import calendar
from datetime import date, datetime, timedelta
import heapq
import json
import holidays as hm
import pycountry as pc
import uuid
from database import insert_into_table, get_holidays_by_uid, update_holidays
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


def isholi(day, holidays):
    days = (0, 1, 2, 3, 4, 5, 6)
    dictKeys = ("All-Mondays", "All-Tuesdays", "All-Wednesdays",
                "All-Thursdays", "All-Fridays", "All-Saturdays", "All-Sundays")
    for i in days:
        if day.weekday() == i and dictKeys[i] in holidays:
            return 1
    if str(day) in holidays:
        return 2
    return 0


def get_calenders_holidays(maxi, maxj, holidays):
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

        var = isholi(maxi, holidays)
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
        for i in range(1, len(highlights_list)):
            if len(highlights_list[i]):
                if year in leaves_dict:
                    leaves_list = leaves_dict[year]
                    leaves = leaves_list[i]
                else:
                    leaves = []
                c = HighlightedCalendar(highlight=highlights_list[i],
                                        leaves=leaves).formatmonth(year, i)
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
    return get_calenders_holidays(maxi, maxj, holidays)


def bestTimeInADateRange(start, end, k):
    i = j = maxi = maxj = start
    k = min(k, 366)

    holidays = {}
    cookie_holidays = request.cookies.get('holidays')
    if cookie_holidays is None:
        holidays['All-Saturdays'] = " "
        holidays['All-Sundays'] = " "
    else:
        holidays = json.loads(cookie_holidays)

    while j <= end:
        if not isholi(j, holidays):
            k -= 1
        if k < 0:
            if (j - i).days > (maxj - maxi).days:
                maxi = i
                maxj = j
            while i <= j and isholi(i, holidays):
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
    return get_calenders_holidays(maxi, maxj, holidays)


def topChoices(heap, holidays):
    choices = CHOICES  # top m choices
    contextList = []
    heapq.heapify(heap)
    while choices:
        h, maxi, maxj = heapq.heappop(heap)
        maxj -= timedelta(days=1)
        contextList.append(get_calenders_holidays(maxi, maxj, holidays))
        choices -= 1
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
        if not isholi(j, holidays):
            k -= 1
        if k < 0:
            yearList.append((-(j - i).days, i, j))
            while i <= j and isholi(i, holidays):
                i += timedelta(days=1)
            k += 1
            i += timedelta(days=1)
        yearList.append((-(j - i).days, i, j))

        j += timedelta(days=1)
    yearList.append((-(j - i).days, i, j))
    return topChoices(yearList, holidays)


def generate_link(uid, config):
    try:
        insert_config = (uid, ) + config
        insert_into_table(insert_config)
        return f'{DOMAIN_NAME}/l/{uid}'
    except Exception as e:
        try:
            update_config = config + (uid, )
            update_holidays(update_config)
            return f'{DOMAIN_NAME}/l/{uid}'
        except Exception as se:
            print(se)
        print(e)
    return ''


@app.route('/', methods=['GET', 'POST'])
def home():
    # Render the page
    if request.method == "POST":
        cookie_holidays = request.cookies.get('holidays')
        cookie_country = request.cookies.get('country')
        cookie_uid = request.cookies.get('uid')
        cookie_subdiv = request.cookies.get('subdiv')
        if 'rrr' in request.form:
            yy = mm = None
            start = request.form.get('start')
            end = request.form.get('end')
            k = int(request.form.get('k'))
            dstart = datetime.strptime(start, "%Y-%m-%d").date()
            dend = datetime.strptime(end, "%Y-%m-%d").date()
            maxholidays, calendars = bestTimeInADateRange(dstart, dend, k)
            config = (yy, mm, start, end, k, cookie_country, cookie_subdiv,
                      cookie_holidays)
            return render_template(
                'dateview.html',
                noHolidays=len(maxholidays),
                k=k,
                start=start,
                end=end,
                holidays=maxholidays,
                calendars=calendars,
                last=maxholidays[len(maxholidays) - 1][0],
                url= generate_link(cookie_uid, config)
            )
        else:
            yy = int(request.form.get('yy'))
            mm = int(request.form.get('mm'))
            k = int(request.form.get('k'))
            start = end = None
            if 'mmm' in request.form:
                config = (yy, mm, start, end, k, cookie_country, cookie_subdiv,
                          cookie_holidays)
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
                    url= generate_link(cookie_uid, config)
                )
            else:
                mm = None
                config = (yy, mm, start, end, k, cookie_country, cookie_subdiv,
                          cookie_holidays)
                yearList = bestTimeInYear(yy, k)
                return render_template(
                    'yearView.html',
                    yearList=yearList,
                    k=k,
                    choices=CHOICES,
                    year=yy,
                    url= generate_link(cookie_uid, config)
                )
    current_year = date.today().year
    country = get_country(get_ip())
    if country is None:
        country = DEFAULT_COUNTRY_CODE
    resp = make_response(render_template('index.html', year=current_year))
    if 'uid' not in request.cookies:
        resp.set_cookie('uid', get_uuid())
    if 'holidays' not in request.cookies:
        init_holidays = {}
        init_holidays = get_holidays(country, current_year, '-')
        resp.set_cookie('holidays', json.dumps(init_holidays))
    if 'country' not in request.cookies:
        resp.set_cookie('country', country)
    if 'subdiv' not in request.cookies:
        resp.set_cookie('subdiv', '-')
    return resp


def get_holidays(country, current_year, subdiv):
    country_holidays = {}
    country_holidays['All-Saturdays'] = " "
    country_holidays['All-Sundays'] = " "
    try:
        if subdiv != '-':
            national_holidays = hm.country_holidays(
                country, subdiv=subdiv, years=[current_year, current_year + 1])
        else:
            national_holidays = hm.country_holidays(
                country, years=[current_year, current_year + 1])
        for day, name in national_holidays.items():
            country_holidays[str(day)] = name
        if country == DEFAULT_COUNTRY_CODE:
            country_holidays |= allHolidays
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


def get_country_names(country_code):
    names = []
    default_country_name = 'INDIA'
    for countryCode in hm.list_supported_countries():
        if countryCode == country_code:
            default_country_name = (countryCode,
                                    pc.countries.get(alpha_2=countryCode).name)
        elif len(countryCode) == 2:
            names.append(
                (countryCode, pc.countries.get(alpha_2=countryCode).name))
    return names, default_country_name


def get_subdiv_names(country):
    subdivs = hm.country_holidays(country).subdivisions
    return subdivs


def encode_spaces(s):
    lis = []
    for c in s:
        if c != ' ':
            lis.append(c)
        else:
            lis.append('+')
    return "".join(lis)


def decode_spaces(s):
    lis = []
    for c in s:
        if c == '+':
            lis.append(' ')
        else:
            lis.append(c)
    return "".join(lis)


@app.route('/holiday', methods=['GET', 'POST'])
def holiday():
    holidays = request.cookies.get('holidays')
    cookie_country_code = request.cookies.get('country')
    cookie_sub_div = request.cookies.get('subdiv')
    if holidays is None or cookie_country_code is None or cookie_sub_div is None:
        return redirect(url_for('.home'))
    cookie_sub_div = decode_spaces(cookie_sub_div)
    allCountries, defaultCountry = get_country_names(cookie_country_code)
    sub_div_names = get_subdiv_names(cookie_country_code)
    if request.method == "POST":
        if 'country' in request.form:
            country, subdiv = request.form.get('country'), request.form.get(
                'subdiv')
            if country != cookie_country_code:
                subdiv = '-'
            new_holidays = get_holidays(country, date.today().year, subdiv)
            subdiv = encode_spaces(subdiv)
            resp = make_response(
                redirect(url_for('.holiday', _external=True, _scheme="https")))
            resp.set_cookie('holidays', json.dumps(new_holidays))
            resp.set_cookie('country', country)
            resp.set_cookie('subdiv', subdiv)
            return resp
        else:
            holidays = request.cookies.get('holidays')
            dictHoliday = json.loads(holidays)
            try:
                if 'mul' in request.form:
                    key, val = request.form.get('week'), ' '
                    key = key.strip()
                    dictHoliday[key] = val
                else:
                    key, val = request.form.get('pick'), request.form.get(
                        'val')
                    key, val = key.strip(), val.strip()
                    dictHoliday[key] = val
                    dictHoliday = dict(sorted(dictHoliday.items()))
                resp = make_response(
                    redirect(
                        url_for('.holiday', _external=True, _scheme="https")))
                resp.set_cookie('holidays', json.dumps(dictHoliday))
                return resp
            except Exception as e:
                print(e)
    return render_template('hview.html',
                           days=json.loads(holidays),
                           countries=allCountries,
                           defaultCountry=defaultCountry,
                           subdivs=sub_div_names,
                           defaultSub=cookie_sub_div)


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


def get_uuid():
    return uuid.uuid4().hex


@app.route('/l/<uid>', methods=['GET', 'POST'])
def render_link(uid):
    config = get_holidays_by_uid(uid)
    print('c', config)
    if config is not None:
        keys = [
            'yy', 'mm', 'start', 'end', 'k', 'country', 'subdiv', 'holidays'
        ]
        dataDict = {}
        for i in range(1, len(config)):
            dataDict[keys[i - 1]] = config[i]
            

        if 'redirect' not in request.cookies:
            resp = make_response(redirect(url_for('.render_link', uid=uid, _external=True, _scheme="https")))
            resp.set_cookie('holidays', dataDict['holidays'])
            resp.set_cookie('country', dataDict['country'])
            resp.set_cookie('subdiv', dataDict['subdiv'])
            if 'uid' not in request.cookies:
                resp.set_cookie('uid', get_uuid())
            resp.set_cookie('redirect', '',expires=0)
            return resp
        else:
            cookie_uid = request.cookies.get('uid')
            config = (dataDict['yy'], dataDict['mm'], dataDict['start'],
                      dataDict['end'], dataDict['k'], dataDict['country'],
                      dataDict['subdiv'], dataDict['holidays'])
            url = generate_link(cookie_uid, config)
            k = int(dataDict['k'])
            if dataDict['mm'] is not None:
                yy, mm = int(dataDict['yy']), int(dataDict['mm'])
                maxholidays, calendars = bestTimeInAMonth(yy, mm, k)
                resp = make_response(
                    render_template(
                        'view.html',
                        noHolidays=len(maxholidays),
                        k=k,
                        month=calendar.month_name[mm],
                        holidays=maxholidays,
                        calendars=calendars,
                        last=maxholidays[len(maxholidays) - 1][0],
                        url = url
                    ))
                return resp
            elif dataDict['start'] is not None:
                start, end = dataDict['start'], dataDict['end']
                dstart = datetime.strptime(start, "%Y-%m-%d").date()
                dend = datetime.strptime(end, "%Y-%m-%d").date()
                maxholidays, calendars = bestTimeInADateRange(dstart, dend, k)
                resp = make_response(
                    render_template(
                        'dateview.html',
                        noHolidays=len(maxholidays),
                        k=k,
                        start=start,
                        end=end,
                        holidays=maxholidays,
                        calendars=calendars,
                        last=maxholidays[len(maxholidays) - 1][0],
                        url = url
                    ))
                return resp
            else:
                yy = int(dataDict['yy'])
                yearList = bestTimeInYear(yy, k)
                resp = make_response(
                    render_template(
                        'yearView.html',
                        yearList=yearList,
                        k=k,
                        choices=CHOICES,
                        year=yy,
                        url = url
                    ))
                return resp
    return abort(404)


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
DOMAIN_NAME = 'https://vacationtime.herokuapp.com'

if __name__ == '__main__':
    # Run the app server on localhost:5000
    app.run()
