# -*- coding:utf8 -*-
import io
import re
import json
import datetime
from urllib import quote_plus
from decimal import Decimal, localcontext
import requests
from PIL import Image
from dateutil import parser
from django.db import connection

from django.contrib.auth.decorators import user_passes_test


DEFAULT_FLAG_SIZES = (32, 128)

#-------------------------------------------------------------------------------
def custom_sql_as_dict(sql, args):
    cursor = connection.cursor()
    cursor.execute(sql, args)
    description = cursor.description
    return [
        dict(zip([column[0] for column in description], row))
        for row in cursor.fetchall()
    ]



#-------------------------------------------------------------------------------
superuser_required = user_passes_test(
    lambda u: u.is_authenticated() and u.is_active and u.is_superuser
)


#===============================================================================
class _ParserInfo(parser.parserinfo):
    parser.parserinfo.MONTHS[8] += ('Sept',)
    parser.parserinfo.WEEKDAYS[1] += ('Tues',)
    parser.parserinfo.WEEKDAYS[2] += ('Weds', 'Wedn')
    parser.parserinfo.WEEKDAYS[3] += ('Thurs', 'Thur')


_parser_info = _ParserInfo()

#-------------------------------------------------------------------------------
def dt_parse(dtstr, **kws):
    return parser.parse(dtstr, _parser_info, **kws)


#-------------------------------------------------------------------------------
def nice_url(text):
    return quote_plus(text.encode('utf8'))


#-------------------------------------------------------------------------------
def get_url_content(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    
    return r.content


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
        ([+-]?\d+)[\xba\xb0]\s*
        (?:(\d+)['\u2032])?\s*
        (?:(\d+)["\u2033])?\s*
        ([NS])?
        \s*,?\s*
        ([+-]?\d+)[\xba\xb0]\s*
        (?:(\d+)['\u2032])?\s*
        (?:(\d+)["\u2033])?\s*
        ([EW])?
    ''',
    re.VERBOSE
)


latlon_dec_re = re.compile(
    ur'''
        ([+-]?\d+\.\d+)
        \s*,?\s*
        ([+-]?\d+\.\d+)
    ''',
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
    m = latlon_sym_re.search(s.strip())
    if m:
        lat_d, lat_m, lat_s, lat_dir, lon_d, lon_m, lon_s, lon_dir = m.groups()
        lat = make_decimal_value(lat_d, lat_m, lat_s, lat_dir.lower() == 's')
        lon = make_decimal_value(lon_d, lon_m, lon_s, lon_dir.lower() == 'w')
        
        return [lat, lon]
    
    m = latlon_dec_re.search(s)
    if m:
        return [Decimal(d) for d in m.groups()]
        
    raise ValueError('Invalid Lat/Lon value: %s' % (s,))


DATE_FORMAT     = "%Y/%m/%d"
TIME_FORMAT     = "%H:%M:%S"
DATETIME_FORMAT = '%s %s' % (DATE_FORMAT, TIME_FORMAT)

parse_date = lambda o: datetime.date(*[int(i) for i in o.split('/')])
parse_time = lambda o: datetime.time(*[int(i) for i in o.split(':')])

#-------------------------------------------------------------------------------
def parse_datetime(o):
    dt, tm = o.split()
    return datetime.datetime.combine(parse_date(dt), parse_time(tm))


PARSERS = dict(
    datetime = parse_datetime,
    date     = parse_date,
    time     = parse_time,
    decimal  = Decimal
)


#-------------------------------------------------------------------------------
def object_hook(dct):
    content_type = dct.get('content_type')
    if content_type in PARSERS:
        return PARSERS[content_type](dct['value'])

    return dct


#===============================================================================
class JargonEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time and decimal types.
    """

    #---------------------------------------------------------------------------
    def _special(self, ctype, value):
        return dict(content_type=ctype, value=value)
        
    #---------------------------------------------------------------------------
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return self._special('datetime', value=o.strftime(DATETIME_FORMAT))
        elif isinstance(o, datetime.date):
            return self._special('date', value=o.strftime(DATE_FORMAT))
        elif isinstance(o, datetime.time):
            return self._special('time', value=o.strftime(TIME_FORMAT))
        elif isinstance(o, Decimal):
            return self._special('decimal', value=str(o))
        return super(JargonEncoder, self).default(o)



#-------------------------------------------------------------------------------
def json_dumps(obj, cls=JargonEncoder, **kws):
    return json.dumps(obj, kws.pop('indent', 4), cls=cls, **kws)


#-------------------------------------------------------------------------------
def json_loads(s, object_hook=object_hook, **kws):
    return json.loads(s, object_hook=object_hook, **kws)


#-------------------------------------------------------------------------------
def json_encoding_test():
    data = dict(
        a_date=datetime.date(2011, 4, 22),
        a_time=datetime.time(16, 59, 59),
        a_datetime=datetime.datetime(2009, 2, 9, 8, 15),
        a_decimal=Decimal('19.65')
    )
    out = dumps(data)
    print out
    result = loads(out)
    print result
    print result == data
    

#-------------------------------------------------------------------------------
def lat_lon_test():
    a = u'º'
    b = u'°'
    print a == b
    print repr(a), repr(b)
    ll = '42º23′'
    #print 'll', parse_latlon(ll.decode('utf8'))

    us = u'41\xba 23\u2032 0\u2033 N, 2\xba 11\u2032 0\u2033 E'
    s1 = '41º23′N 2°11′E'
    s2 = '-41° 23′ 7″ N, 2° 11′ 0″ E'
    s3 = '41º,11°'

    print 'us', parse_latlon(us)
    print 's1', parse_latlon(s1.decode('utf8'))
    print 's2', parse_latlon(s2.decode('utf8'))
    print 's3', parse_latlon(s3.decode('utf8'))
    print 'dc', parse_latlon('12.34, 56.78')


################################################################################
if __name__ == '__main__':
    json_encoding_test()
    lat_lon_test()
