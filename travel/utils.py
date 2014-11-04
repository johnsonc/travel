# -*- coding:utf8 -*-
import io
import re
from decimal import Decimal, localcontext

import requests
from PIL import Image
from path import path

_wiki_flag_url_re =  re.compile(r'(.*)/(\d+)px(.*)')
_default_flag_sizes = (16, 32, 64, 128, 256, 512)


#-------------------------------------------------------------------------------
def get_url_content(url):
    r = requests.get(url)
    if r.status_code != 200:
        raise ValueError('Status %s (%s)' % (r.status_code, url))
    
    return r.content

#-------------------------------------------------------------------------------
def make_resizer(size):
    x1, y1 = size
    return lambda x2: (x2, x2 * y1 / x1)
    
#-------------------------------------------------------------------------------
def get_wiki_flags_by_size(url, sizes=None):
    '''Typical url format:
    
    http://upload.wikimedia.org/wikipedia/commons/thumb/x/yz/Flag_of_XYZ.svg/120px-Flag_of_XYZ.svg.png'''
    data = {}
    sizes = sizes or _default_flag_sizes
    for size in sizes:
        size_url = _wiki_flag_url_re.sub(r'\1/%spx\3' % size, url)
        data[size] = get_url_content(size_url)

    return data

#-------------------------------------------------------------------------------
def get_flags_from_image_by_size(url, sizes=None):
    im = Image.open(io.BytesIO(get_url_content(url)))
    x1, y1 = size = im.size
    resize = make_resizer(size)
    data = {}
    sizes = sizes or _default_flag_sizes
    for x1 in sizes:
        x2, y2 = new_size = resize(x1)
        resample = Image.BICUBIC if x2 > x1 else Image.ANTIALIAS
        stream = io.BytesIO()
        new_im = im.resize(new_size, resample)
        new_im.save(stream, 'PNG')
        data[x1] = stream.getvalue()

    return data

#-------------------------------------------------------------------------------
def send_message(user, title, message):
    from jargon.apps.mailer import send_mail
    send_mail(title, 'From %s: (%s)\n\n%s' % (
        user.get_full_name, 
        user.email,
        message
    ))


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


################################################################################
def test():
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


if __name__ == '__main__':
    test()
