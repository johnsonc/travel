from django.contrib import admin
from travel import models as travel


#===============================================================================
class EntityAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'type',
        'code',
        'name',
        'category',
        'capital',
        'state',
        'country',
        'continent',
    )


#===============================================================================
class EntityTypeAdmin(admin.ModelAdmin):
    list_display = ( 
        'abbr',
        'title',
    )


#===============================================================================
class FlagAdmin(admin.ModelAdmin):
    list_display = ( 
        'id',
        'source',
        'base_dir',
        'ref',
        'width_32',
    )


#===============================================================================
class ProfileAdmin(admin.ModelAdmin):
    list_display = ( 
        'user',
        'access',
    )


#===============================================================================
class ToDoListAdmin(admin.ModelAdmin):
    list_display = ( 
        'id',
        'owner',
        'title',
        'is_public',
        'description',
    )


#===============================================================================
class TravelLogAdmin(admin.ModelAdmin):
    list_display = ( 
        'id',
        'arrival',
        'rating',
        'user',
        'entity',
    )


admin.site.register(travel.Entity, EntityAdmin)
admin.site.register(travel.EntityType, EntityTypeAdmin)
admin.site.register(travel.Flag, FlagAdmin)
admin.site.register(travel.Profile, ProfileAdmin)
admin.site.register(travel.ToDoList, ToDoListAdmin)
admin.site.register(travel.TravelLog, TravelLogAdmin)


