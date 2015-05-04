import operator
from django.db.models import Manager, Q, Count, Min, Max

__all__ = (
    'TravelProfileManager',
    'TravelBucketListManager',
    'TravelEntityManager',
    'TravelLogManager', 
)


#===============================================================================
class TravelProfileManager(Manager):
    
    #---------------------------------------------------------------------------
    def public(self):
        return self.filter(access=self.model.Access.PUBLIC).exclude(user__id=1)

    #---------------------------------------------------------------------------
    def for_user(self, user):
        return self.get_or_create(user=user)[0]


#===============================================================================
class TravelBucketListManager(Manager):
    
    #---------------------------------------------------------------------------
    def for_user(self, user):
        q = Q(is_public=True)
        if user.is_authenticated():
            q |= Q(owner=user)
        return self.filter(q)
        
    #---------------------------------------------------------------------------
    def new_list(self, owner, title, entries, is_public=True, description=''):
        tdl = self.create(
            owner=owner, 
            title=title, 
            is_public=is_public, 
            description=description
        )
        
        for e in entries:
            e.todos.create(todo=tdl)
            
        return tdl


#===============================================================================
class TravelEntityManager(Manager):

    #---------------------------------------------------------------------------
    @staticmethod
    def _search_q(term):
        return (
            Q(name__icontains=term)      |
            Q(full_name__icontains=term) |
            Q(locality__icontains=term)  |
            Q(code__iexact=term)
        )
        
    #---------------------------------------------------------------------------
    def search(self, term, type=None):
        term = term.strip() if term else term
        qs = None
        if term:
            qs = self.filter(self._search_q(term))
        
        if type:
            qs = qs or self
            qs = qs.filter(type__abbr=type)
            
        return self.none() if qs is None else qs
    
    #---------------------------------------------------------------------------
    def advanced_search(self, bits, type=None):
        qq = reduce(operator.ior, [self._search_q(term) for term in bits])
        qs = self.filter(qq)
        return qs.filter(type__abbr=type) if type else qs
    
    #---------------------------------------------------------------------------
    def countries(self):
        return self.filter(type__abbr='co')
    
    #---------------------------------------------------------------------------
    def country(self, code):
        return self.get(code=code, type__abbr='co')

    #---------------------------------------------------------------------------
    def country_dict(self):
        return dict([(e.code, e) for e in self.countries()])


#===============================================================================
class TravelLogManager(Manager):

    #---------------------------------------------------------------------------
    def checklist(self, user):
        return dict(
            self.filter(user=user).values_list('entity').annotate(count=Count('entity'))
        )
