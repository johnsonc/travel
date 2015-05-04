from django.contrib import admin
from travel import models as travel


#===============================================================================
class TravelEntityAdmin(admin.ModelAdmin):
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
class TravelEntityTypeAdmin(admin.ModelAdmin):
    list_display = ('abbr', 'title')


#===============================================================================
class TravelFlagAdmin(admin.ModelAdmin):
    list_display = ('id', 'source', 'base_dir', 'ref', 'thumb')


#===============================================================================
class TravelProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'access')


#===============================================================================
class TravelBucketListAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'title', 'is_public', 'description')


#===============================================================================
class TravelLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'arrival', 'rating', 'user', 'entity')


admin.site.register(travel.TravelEntity, TravelEntityAdmin)
admin.site.register(travel.TravelEntityType, TravelEntityTypeAdmin)
admin.site.register(travel.TravelFlag, TravelFlagAdmin)
admin.site.register(travel.TravelProfile, TravelProfileAdmin)
admin.site.register(travel.TravelBucketList, TravelBucketListAdmin)
admin.site.register(travel.TravelLog, TravelLogAdmin)


