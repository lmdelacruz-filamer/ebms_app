from django.contrib import admin
from .models import Categories, Equipments, Borrowers, BorrowRecords

# Register your models here.

admin.site.register(Categories)
admin.site.register(Equipments)
admin.site.register(Borrowers)
admin.site.register(BorrowRecords)
