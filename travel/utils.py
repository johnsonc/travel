# -*- coding:utf8 -*-
import re
from decimal import Decimal, localcontext

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
