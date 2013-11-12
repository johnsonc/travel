from django.contrib import admin
from travel import models as travel


#===============================================================================
# class FooInline(admin.TabularInline):
#    model = foo.Foo
#    extra = 3


#===============================================================================
# class BoilerplateAdmin(admin.ModelAdmin):

    #---------------------------------------------------------------------------
    # def custom_list_field_html(self):
    #     return '<span>Foo</span>'
    # custom_list_field_html.allow_tags        = true
    # custom_list_field_html.admin_order_field = 'foo'
    # custom_list_field_html.boolena           = True


# The following classes define the admin interface for your models.
# See http://bit.ly/xAegih for all options you can use in these classes.


#===============================================================================
class EntityAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'type',
        'code',
        'name',
        'category',
        'locality',
        'flag',
        'capital',
        'state',
        'country',
        'continent',
    )
    
    # exclude             = ('',)
    # filter_horizontal   = ('',)
    # inlines             = (,)
    # list_filter         = ('',)
    # list_per_page       = 100
    # list_select_related = False
    # ordering            = ('',)
    # readonly_fields     = ('',)
    # search_fields       = ('',)



#===============================================================================
class EntityTypeAdmin(admin.ModelAdmin):
    list_display = ( 
        'abbr',
        'title',
    )
    
    # exclude             = ('',)
    # filter_horizontal   = ('',)
    # inlines             = (,)
    # list_filter         = ('',)
    # list_per_page       = 100
    # list_select_related = False
    # ordering            = ('',)
    # readonly_fields     = ('',)
    # search_fields       = ('',)



#===============================================================================
class FlagAdmin(admin.ModelAdmin):
    list_display = ( 
        'id',
        'source',
        'base_dir',
        'ref',
        'width_16',
        'width_32',
        'width_64',
        'width_128',
        'width_256',
        'width_512',
    )
    
    # exclude             = ('',)
    # filter_horizontal   = ('',)
    # inlines             = (,)
    # list_filter         = ('',)
    # list_per_page       = 100
    # list_select_related = False
    # ordering            = ('',)
    # readonly_fields     = ('',)
    # search_fields       = ('',)


#===============================================================================
class ProfileAdmin(admin.ModelAdmin):
    list_display = ( 
        'user',
        'access',
    )
    
    # exclude             = ('',)
    # filter_horizontal   = ('',)
    # inlines             = (,)
    # list_filter         = ('',)
    # list_per_page       = 100
    # list_select_related = False
    # ordering            = ('',)
    # readonly_fields     = ('',)
    # search_fields       = ('',)


#===============================================================================
class ToDoListAdmin(admin.ModelAdmin):
    list_display = ( 
        'id',
        'owner',
        'title',
        'is_public',
        'description',
    )
    
    # exclude             = ('',)
    # filter_horizontal   = ('',)
    # inlines             = (,)
    # list_filter         = ('',)
    # list_per_page       = 100
    # list_select_related = False
    # ordering            = ('',)
    # readonly_fields     = ('',)
    # search_fields       = ('',)


#===============================================================================
class TravelLogAdmin(admin.ModelAdmin):
    list_display = ( 
        'id',
        'arrival',
        'rating',
        'user',
        'entity',
    )


# Each of these lines registers the admin interface for one model. If
# you don't want the admin interface for a particular model, remove
# the line which registers it.
admin.site.register(travel.Entity, EntityAdmin)
admin.site.register(travel.EntityType, EntityTypeAdmin)
admin.site.register(travel.Flag, FlagAdmin)
admin.site.register(travel.Profile, ProfileAdmin)
admin.site.register(travel.ToDoList, ToDoListAdmin)
admin.site.register(travel.TravelLog, TravelLogAdmin)


