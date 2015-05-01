import json
from django.shortcuts import render
from travel import models as travel

FLAG_GROUPS = [
    [u'AT', u'LV', u'PE', u'PF'],
    [u'AX', u'FO', u'NO', u'IS'],
    [u'XE', u'GE', u'XI', u'DK'],
    [u'HR', u'SK', u'SI', u'RS'],
    [u'RU', u'BG', u'LU', u'NL'],
    [u'LT', u'BO', u'GH', u'ET'],
    [u'XW', u'LK', u'BT', u'AL'],
    [u'TD', u'RO', u'AD', u'MD'],
    [u'GN', u'ML', u'SN', u'CM'],
    [u'BF', u'MM', u'GH', u'GW'],
    [u'ZW', u'UG', u'MU', u'CF'],
    [u'JO', u'PS', u'SS', u'KW'],
    [u'BE', u'DE', u'AM', u'TD'],
    [u'VU', u'ZA', u'GY', u'ER'],
    [u'CR', u'TH', u'CU', u'SR'],
    [u'AU', u'NZ', u'TC', u'CK'],
    [u'BH', u'QA', u'MT', u'NP'],
    [u'AR', u'HN', u'SV', u'NI'],
    [u'EG', u'YE', u'SY', u'IQ'],
    [u'IR', u'TJ', u'HU', u'BG'],
    [u'BW', u'GM', u'TZ', u'TT'],
    [u'GR', u'UY', u'LR', u'MY'],
    [u'CD', u'NA', u'KN', u'CG'],
    [u'LA', u'NE', u'GL', u'BD'],
    [u'NG', u'NF', u'LB', u'LS'],
    [u'AZ', u'UZ', u'EH', u'KM'],
    [u'PL', u'MC', u'ID', u'SG'],
    [u'TN', u'TR', u'MA', u'MR'],
    [u'DZ', u'MR', u'PK', u'TR'],
    [u'FI', u'SE', u'DK', u'XE'],
    [u'SC', u'MU', u'CF', u'KM'],
    [u'DO', u'PA', u'MQ', u'BI'],
    [u'AG', u'BB', u'BA', u'LC'],
    [u'EC', u'CO', u'VE', u'AM'],
    [u'HK', u'IM', u'KG', u'AL'],
    [u'CI', u'IE', u'IT', u'IN'],
    [u'BD', u'JP', u'PW', u'GL'],
    [u'AS', u'MX', u'MD', u'ME'],
    [u'AF', u'LY', u'KN', u'MW'],
    [u'MH', u'NR', u'SB', u'CW'],
    [u'BY', u'KZ', u'TM', u'IR'],
    [u'CL', u'TO', u'TW', u'TG'],
    [u'BJ', u'MG', u'OM', u'AE'],
    [u'SL', u'UZ', u'RW', u'VC'],
    [u'FM', u'AW', u'SO', u'TV'],
    [u'GD', u'GP', u'DM', u'MV'],
    [u'FJ', u'VG', u'AI', u'MS'],
    [u'GQ', u'DJ', u'BS', u'PH'],
    [u'AQ', u'CY', u'XK', u'MO'],
    [u'LI', u'SM', u'VA', u'GI'],
    [u'EE', u'GA', u'UA', u'SL'],
    [u'IO', u'KI', u'CK'],
    [u'AO', u'KE', u'SZ', u'ZM'],
    [u'BZ', u'CV', u'SX', u'CZ'],
    [u'FK', u'KY', u'BM', u'TV'],
    [u'VN', u'CN', u'TW', u'KP'],
    [u'SD', u'PS', u'JO', u'EH'],
    [u'HT', u'LI', u'PT', u'MN'],
    [u'PG', u'CX', u'CC', u'WS'],
    [u'XS', u'XI', u'FI', u'XE'],
    [u'JM', u'MK', u'ST', u'SC'],
    [u'AO', u'MZ', u'SZ', u'KE'],
    [u'BN', u'KH', u'TL', u'TK'],
    [u'FR', u'IE', u'IT', u'CI'],
    [u'GT', u'MX', u'PY', u'AR']
]

EXCLUDED_IDS = [u'BV', u'CA', u'GF', u'HM', u'YT', u'RE', u'SJ', u'US', u'UM', u'WF']

#-------------------------------------------------------------------------------
def get_flag_game_data():
    countries = dict([
        (co.code, {"name": co.name, "id": co.code, "small": co.flag.thumb.url, "large": co.flag.large.url})
        for co in travel.TravelEntity.objects.countries().exclude(code__in=EXCLUDED_IDS)
    ])
    return {'countries': json.dumps(countries), 'groups': json.dumps(FLAG_GROUPS)}

#-------------------------------------------------------------------------------
def flag_game(request):
    data = get_flag_game_data()
    return render(request, 'travel/quiz/flags.html', data)

