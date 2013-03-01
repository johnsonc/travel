import re

from django.conf import settings

from path import path
from jargon.apps.mailer import send_mail
from travel import models as travel

_flag_url_re =  re.compile(r'(.*)/(\d+)px(.*)')

#-------------------------------------------------------------------------------
def flag_from_wikimedia(obj, url):
    # 'http://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Flag_of_Wyoming.svg/120px-Flag_of_Wyoming.svg.png'
    import httplib2
    
    ref        = obj.code.lower()
    base_dir   = path(obj.flag_dir)
    parent_dir = base_dir / ref
    abs_dir    = settings.MEDIA_ROOT / travel.BASE_FLAG_DIR / parent_dir
    flag_path  = BASE_FLAG_DIR / parent_dir / ('%s-%%s.png' % (ref,))
    
    if not abs_dir.exists():
        abs_dir.makedirs()

    data = {}
    for size in ('16', '32', '64', '128', '256', '512'):
        size_url = _flag_url_re.sub(r'\1/%spx\3' % size, url)
        h = httplib2.Http()
        try:
            r, bytes = h.request(size_url)
        except httplib2.ServerNotFoundError, why:
            raise Exception, '%s (%s)' % (why, size_url)
        
        if r.status != 200:
            raise Exception, 'Status %s (%s)' % (r.status, size_url)
        
        data[settings.MEDIA_ROOT / (flag_path % size)] = bytes

    if obj.flag:
        obj.flag.delete()
    
    for fn, bytes in data.iteritems():
        fp = open(fn, 'wb')
        fp.write(bytes)
        fp.close()

    return travel.Flag.objects.create(
        source=url,
        base_dir=base_dir,
        ref=ref,
        width_16=flag_path  %  16,
        width_32=flag_path  %  32,
        width_64=flag_path  %  64,
        width_128=flag_path % 128,
        width_256=flag_path % 256,
        width_512=flag_path % 512,
    )


#-------------------------------------------------------------------------------
def send_message(user, title, message):
    send_mail(title, 'From %s: (%s)\n\n%s' % (
        user.get_full_name, 
        user.email,
        form.cleaned_data['message']
    ))
