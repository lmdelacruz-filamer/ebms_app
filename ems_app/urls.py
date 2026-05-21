from django.urls import path
from . import views
from django.contrib import admin

urlpatterns = [
    path('login', views.login_view),
    path('logout', views.logout_view),
    path('', views.dashboard),
    path('home', views.dashboard),
    path('borrower/list', views.borrower_list),
    path('borrower/add', views.add_borrower),
    path('borrower/edit/<int:borrowerId>', views.edit_borrower),
    path('borrower/delete/<int:borrowerId>', views.delete_borrower),
    path('category/list', views.category_list),
    path('category/add', views.add_category),
    path('category/edit/<int:categoryId>', views.edit_category),
    path('category/delete/<int:categoryId>', views.delete_category),
    path('equipment/list', views.equipment_list),
    path('equipment/add', views.add_equipment),
    path('equipment/edit/<int:equipmentId>', views.edit_equipment),
    path('equipment/delete/<int:equipmentId>', views.delete_equipment),
    path('borrow', views.borrow_form),
    path('borrow/save', views.save_borrow),
    path('returns', views.returns_list),
    path('returns/process/<int:recordId>', views.process_return),
    # API - used by the cascading dropdown on the borrow page
    path('api/equipment-by-category', views.get_equipment_by_category),
]
