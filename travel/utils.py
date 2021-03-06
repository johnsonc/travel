# -*- coding:utf8 -*-
import io
import re
import json
import datetime
from urllib import quote_plus
from decimal import Decimal, localcontext
import requests
from PIL import Image
from dateutil import parser as dt_parser


DEFAULT_FLAG_SIZES = (32, 128)

# from django.db import connection
# #-------------------------------------------------------------------------------
# def custom_sql_as_dict(sql, args):
#     cursor = connection.cursor()
#     cursor.execute(sql, args)
#     description = cursor.description
#     return [
#         dict(zip([column[0] for column in description], row))
#         for row in cursor.fetchall()
#     ]





#===============================================================================
class DateParserInfo(dt_parser.parserinfo):
    dt_parser.parserinfo.MONTHS[8] += ('Sept',)
    dt_parser.parserinfo.WEEKDAYS[1] += ('Tues',)
    dt_parser.parserinfo.WEEKDAYS[2] += ('Weds', 'Wedn')
    dt_parser.parserinfo.WEEKDAYS[3] += ('Thurs', 'Thur')

_date_parser_info = DateParserInfo()


#-------------------------------------------------------------------------------
def dt_parse(dtstr, **kws):
    return dt_parser.parse(dtstr, _date_parser_info, **kws)


#-------------------------------------------------------------------------------
def nice_url(text):
    return quote_plus(text.encode('utf8'))


#-------------------------------------------------------------------------------
def get_url_content(url):
    r = requests.get(url)
    return r.content if r.ok else None


#-------------------------------------------------------------------------------
def make_resizer(size):
    x1, y1 = size
    return lambda x2: (x2, x2 * y1 / x1)


#-------------------------------------------------------------------------------
def get_wiki_flags_from_svg(url):
    '''Typical url format:

    http://upload.wikimedia.org/wikipedia/commons/x/yz/Flag_of_XYZ.svg
    
    http://upload.wikimedia.org/wikipedia/commons/thumb/x/yz/Flag_of_XYZ.svg/120px-Flag_of_XYZ.svg.png
    '''
    data = [get_url_content(url)]
    for size in DEFAULT_FLAG_SIZES:
        pth, base = url.rsplit('/', 1)
        size_url = '{}/{}/{}px-{}.png'.format(
            pth.replace('/commons/', '/commons/thumb/'),
            base,
            size,
            base
        )
        
        data.append(get_url_content(size_url))

    return data


#-------------------------------------------------------------------------------
def get_flag_data(url):
    norm_url = url.lower()
    if norm_url.endswith('.svg'):
        svg, thumb, large = get_wiki_flags_from_svg(url)
        return svg, thumb, large
    else:
        thumb, large = get_flags_from_image_by_size(url)
        return None, thumb, large


#-------------------------------------------------------------------------------
def get_flags_from_image_by_size(url):
    im = Image.open(io.BytesIO(get_url_content(url)))
    x1, y1 = size = im.size
    resize = make_resizer(size)
    data = []
    for x1 in DEFAULT_FLAG_SIZES:
        x2, y2 = new_size = resize(x1)
        resample = Image.BICUBIC if x2 > x1 else Image.ANTIALIAS
        stream = io.BytesIO()
        new_im = im.resize(new_size, resample)
        new_im.save(stream, 'PNG')
        data.append(stream.getvalue())

    return data


latlon_sym_re = re.compile(
    ur'''
        ([+-]?\d+)[\xba\xb0]?\s*
        (?:(\d+)['\u2032])?\s*
        (?:(\d+)["\u2033])?\s*
        ([NS])?
        \s*[,/]?\s*
        ([+-]?\d+)[\xba\xb0]?\s*
        (?:(\d+)['\u2032])?\s*
        (?:(\d+)["\u2033])?\s*
        ([EW])?
    ''',
    re.VERBOSE
)


latlon_dec_re = re.compile(
    ur'''^
        ([+-]?\d+\.\d+)
        \s*[,/]?\s*
        ([+-]?\d+\.\d+)
    $''',
    re.VERBOSE
)

#-------------------------------------------------------------------------------
def make_decimal_value(degs='0', mins=None, secs=None, negative=False):
    with localcontext() as ctx:
        ctx.prec = 6
        degs, mins, secs = Decimal(degs), Decimal(mins or '0'), Decimal(secs or '0')
        degs += (mins / Decimal('60')) + (secs / Decimal('3600'))
        return -degs if negative else degs


#-------------------------------------------------------------------------------
def parse_latlon(s):
    m = latlon_dec_re.search(s)
    if m:
        return [Decimal(d) for d in m.groups()]

    m = latlon_sym_re.search(s.strip())
    if m:
        lat_d, lat_m, lat_s, lat_dir, lon_d, lon_m, lon_s, lon_dir = m.groups()
        lat_dir = lat_dir or 'N'
        lon_dir = lon_dir or 'E'
        lat = make_decimal_value(lat_d, lat_m, lat_s, lat_dir.lower() == 's')
        lon = make_decimal_value(lon_d, lon_m, lon_s, lon_dir.lower() == 'w')
        
        return [lat, lon]
    
    raise ValueError('Invalid Lat/Lon value: %s' % (s,))


#===============================================================================
class TravelJsonEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time and decimal types.
    """
    
    DATE_FORMAT     = "%Y-%m-%d"
    TIME_FORMAT     = "%H:%M:%S"
    DATETIME_FORMAT = '{}T{}Z'.format(DATE_FORMAT, TIME_FORMAT)
    
    #---------------------------------------------------------------------------
    def _special(self, ctype, value):
        return {'content_type': ctype, 'value': value}
        
    #---------------------------------------------------------------------------
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return self._special('datetime', o.strftime(self.DATETIME_FORMAT))
        elif isinstance(o, datetime.date):
            return self._special('date', o.strftime(self.DATE_FORMAT))
        elif isinstance(o, datetime.time):
            return self._special('time', o.strftime(self.TIME_FORMAT))
        elif isinstance(o, Decimal):
            return self._special('decimal', str(o))
        
        return super(TravelJsonEncoder, self).default(o)


DATETIME_PARSERS = dict(
    datetime = lambda o: datetime.datetime.strptime(o, TravelJsonEncoder.DATETIME_FORMAT),
    date     = lambda o: datetime.date(*[int(i) for i in o.split('/')]),
    time     = lambda o: datetime.time(*[int(i) for i in o.split(':')]),
    decimal  = Decimal
)


#-------------------------------------------------------------------------------
def object_hook(dct):
    content_type = dct.get('content_type')
    if content_type in DATETIME_PARSERS:
        return DATETIME_PARSERS[content_type](dct['value'])

    return dct


#-------------------------------------------------------------------------------
def json_dumps(obj, cls=TravelJsonEncoder, **kws):
    return json.dumps(obj, kws.pop('indent', 4), cls=cls, **kws)


#-------------------------------------------------------------------------------
def json_loads(s, object_hook=object_hook, **kws):
    return json.loads(s, object_hook=object_hook, **kws)


#-------------------------------------------------------------------------------
def json_encoding_test():
    print('-' * 40)
    data = dict(
        a_date=datetime.date(2011, 4, 22),
        a_time=datetime.time(16, 59, 59),
        a_datetime=datetime.datetime(2009, 2, 9, 8, 15),
        a_decimal=Decimal('19.65')
    )
    out = json_dumps(data)
    print(out)
    result = json_loads(out)
    print(result)
    print(result == data)
    

#-------------------------------------------------------------------------------
def lat_lon_test():
    print '-' * 40
    a, b = u'º', u'°'
    print a == b, repr(a), repr(b)

    tests = [
        '12.34, 56.78',
        '50°51′N 5°41′E'.decode('utf8'),

        u'41\xb0 23\u2032 0\u2033 N, 2\xb0 11\u2032 0\u2033 E',
        u'12\xb0 N, 56\xb0W',

        u'12.34 N, 56.78 W',

        '41º23′N 2°11′E'.decode('utf8'),
        '-41° 23′ 7″ N, 2° 11′ 0″ E'.decode('utf8'),
        '41º,11°'.decode('utf8'),
    ]
    
    total, good = 0, 0
    for i, test in enumerate(tests):
        total += 1
        print i
        print test
        print repr(test)
        try:
            result = parse_latlon(test)
            good += 1
            print result
        except ValueError as why:
            print '***** {}'.format(why.message)
        print
    print '{} of {} good'.format(good, total)


################################################################################
if __name__ == '__main__':
    json_encoding_test()
    lat_lon_test()
