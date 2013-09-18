import re
from path import path
from django.conf import settings
from jargon.apps.mailer import send_mail
from travel import models as travel


#-------------------------------------------------------------------------------
def send_message(user, title, message):
    send_mail(title, 'From %s: (%s)\n\n%s' % (
        user.get_full_name, 
        user.email,
        form.cleaned_data['message']
    ))


_flag_url_re =  re.compile(r'(.*)/(\d+)px(.*)')


#===============================================================================
class WikiFlagUtil(object):
    
    #---------------------------------------------------------------------------
    def __init__(self, url, entity):
        self.entity   = entity
        self.sizes    = {}
        self.url      = url
        self.base_dir = path(entity.flag_dir)
        
    #---------------------------------------------------------------------------
    def save(self):
        ref         = self.entity.code.lower()
        static_root = path(settings.STATIC_ROOT)
        parent_dir  = path(travel.BASE_FLAG_DIR) / self.base_dir / ref
        abs_dir     = static_root / parent_dir

        if not abs_dir.exists():
            abs_dir.makedirs()

        flag_path_fmt = parent_dir / ('%s-%%s.png' % (ref,))
        flag          = self.entity.flag or travel.Flag()
        flag.source   = self.url
        flag.base_dir = self.base_dir
        flag.ref      = ref

        for size, bytes in self.sizes.iteritems():
            setattr(flag, 'width_%s' % size, flag_path_fmt % size)
            with open(static_root / (flag_path_fmt % size), 'wb') as fp:
                fp.write(bytes)

        flag.save()
        if not self.entity.flag:
            self.entity.flag = flag
            self.entity.save()
            
        return flag
    
    #---------------------------------------------------------------------------
    @staticmethod
    def create(url, entity):
        import requests
        # http://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Flag_of_Wyoming.svg/120px-Flag_of_Wyoming.svg.png

        flag_util = WikiFlagUtil(url, entity)
        for size in ('16', '32', '64', '128', '256', '512'):
            size_url = _flag_url_re.sub(r'\1/%spx\3' % size, url)
            # print size, size_url
            r = requests.get(size_url)
            if r.status_code != 200:
                raise ValueError('Status %s (%s)' % (r.status_code, size_url))

            flag_util.sizes[size] = r.content

        return flag_util
    