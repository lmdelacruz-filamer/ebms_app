from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator # this is for the pagination and search function.
from django.contrib.auth import authenticate, login, logout # this is for the login system
from django.contrib.auth.decorators import login_required # this protects pages so only logged-in users can see them
from .models import Categories, Equipments, Borrowers, BorrowRecords

# Create your views here.

def login_view(request):
    try:
        # if already logged in, just send them to the dashboard
        if request.user.is_authenticated:
            return redirect('/home')

        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            # this check validation requirements to fill the blank fields
            if not username or not password:
                messages.error(request, 'Please enter both username and password.')
                return render(request, 'auth/Login.html')

            # authenticate checks the username and password against the users table
            userObj = authenticate(request, username=username, password=password)

            if userObj is not None:
                # login() puts the user info into the session so they stay logged in
                login(request, userObj)
                messages.success(request, f'Welcome back, {userObj.username}!')
                return redirect('/home')
            else:
                messages.error(request, 'Invalid username or password. Please try again.')
                return render(request, 'auth/Login.html')

        return render(request, 'auth/Login.html')
    except Exception as e:
        return HttpResponse(f'Error occurred during login: {e}')


def logout_view(request):
    try:
        # logout clears the session so the user is no longer authenticated
        logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('/login')
    except Exception as e:
        return HttpResponse(f'Error occurred during logout: {e}')


@login_required
def dashboard(request):
    try:
        from django.db.models import Sum

        # quantity of each equipment row. represents a pool of identical units
        total_units = Equipments.objects.aggregate(total=Sum('total_quantity'))['total'] or 0
        borrowed_units = BorrowRecords.objects.filter(status='borrowed').aggregate(total=Sum('quantity'))['total'] or 0
        # whatever is left after subtracting out-on-loan is on the shelf
        available_units = total_units - borrowed_units

        total_borrowers = Borrowers.objects.count()
        # this gets the 5 most recent borrow records for the activity list
        recent_borrows = BorrowRecords.objects.order_by('-created_at')[:5]

        data = {
            'current_tab': 'home',
            'total_equipment': total_units,
            'available': available_units,
            'borrowed': borrowed_units,
            'total_borrowers': total_borrowers,
            'recent_borrows': recent_borrows,
        }
        return render(request, 'home/Dashboard.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during load dashboard: {e}')


@login_required
def borrower_list(request):
    try:
        # this is for the search functionality 
        search_query = request.GET.get('search', '')
        if search_query:
            borrowerObj = (
                Borrowers.objects.filter(borrower_name__icontains=search_query) |
                Borrowers.objects.filter(borrower_contact__icontains=search_query) |
                Borrowers.objects.filter(reference_id__icontains=search_query)
            )
        else:
            borrowerObj = Borrowers.objects.all()

        # sort by reference_id so the list regardless of when each borrower was added or last edited
        borrowerObj = borrowerObj.order_by('reference_id')

        # this one is for pagination. 15 borrowers per page only
        paginator = Paginator(borrowerObj, 15)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        data = {
            'current_tab': 'borrowers',
            'borrowers': page_obj,
            'page_obj': page_obj,
            'search_query': search_query, # this sends the search text back so the box is not empty
        }
        return render(request, 'borrower/BorrowersList.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during load borrowers: {e}')


@login_required
def add_borrower(request):
    try:
        if request.method == 'POST':
            referenceId = request.POST.get('reference_id')
            borrowerName = request.POST.get('borrower_name')
            borrowerContact = request.POST.get('borrower_contact')
            borrowerAddress = request.POST.get('borrower_address')

            # this check validation requirements to fill the blank fields
            if not referenceId or not borrowerName or not borrowerContact or not borrowerAddress:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'borrower/AddBorrower.html')

            # this checks for a duplicate reference ID 
            if Borrowers.objects.filter(reference_id=referenceId).exists():
                messages.error(request, f'Reference ID "{referenceId}" is already registered to another borrower.')
                return render(request, 'borrower/AddBorrower.html')

            Borrowers.objects.create(
                reference_id=referenceId,
                borrower_name=borrowerName,
                borrower_contact=borrowerContact,
                borrower_address=borrowerAddress,
                active=True,
            )
            messages.success(request, 'Borrower added successfully!')
            return redirect('/borrower/list')
        else:
            return render(request, 'borrower/AddBorrower.html')
    except Exception as e:
        return HttpResponse(f'Error occurred during add borrower: {e}')


@login_required
def edit_borrower(request, borrowerId):
    try:
        borrowerObj = Borrowers.objects.get(pk=borrowerId)

        # this checks if the borrower still has active borrows, if so we cant edit. to avoid comlication in the log list.
        if borrowerObj.borrow_records.filter(status='borrowed').exists():
            messages.error(request, f'Cannot edit "{borrowerObj.borrower_name}" — they still have equipment on borrow. Process the return first.')
            return redirect('/borrower/list')

        if request.method == 'POST':
            referenceId = request.POST.get('reference_id')
            borrowerName = request.POST.get('borrower_name')
            borrowerContact = request.POST.get('borrower_contact')
            borrowerAddress = request.POST.get('borrower_address')

            data = {'borrower': borrowerObj}

            # this check validation requirements to fill the blank fields
            if not referenceId or not borrowerName or not borrowerContact or not borrowerAddress:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'borrower/EditBorrower.html', data)

            # this checks for a duplicate reference ID, excluding the borrower being edited
            if Borrowers.objects.filter(reference_id=referenceId).exclude(pk=borrowerId).exists():
                messages.error(request, f'Reference ID "{referenceId}" is already registered to another borrower.')
                return render(request, 'borrower/EditBorrower.html', data)

            borrowerObj.reference_id = referenceId
            borrowerObj.borrower_name = borrowerName
            borrowerObj.borrower_contact = borrowerContact
            borrowerObj.borrower_address = borrowerAddress
            borrowerObj.save()
            messages.success(request, 'Borrower updated successfully!')

        data = {'borrower': borrowerObj}
        return render(request, 'borrower/EditBorrower.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during edit borrower: {e}')


@login_required
def delete_borrower(request, borrowerId):
    try:
        borrowerObj = Borrowers.objects.get(pk=borrowerId)

        # this checks if the borrower still has active borrows, if so we can't delete
        if borrowerObj.borrow_records.filter(status='borrowed').exists():
            messages.error(request, f'Cannot delete "{borrowerObj.borrower_name}" — they still have equipment on borrow. Process the return first.')
            return redirect('/borrower/list')

        if request.method == 'POST':
            borrowerObj.delete()
            messages.success(request, 'Borrower deleted successfully!')
            return redirect('/borrower/list')

        data = {'borrower': borrowerObj}
        return render(request, 'borrower/DeleteBorrower.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during delete borrower: {e}')


@login_required
def category_list(request):
    try:
        # this is for the search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            categoryObj = Categories.objects.filter(name__icontains=search_query)
        else:
            categoryObj = Categories.objects.all()

        # this one is for pagination. 15 categories per page only
        paginator = Paginator(categoryObj, 15)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        data = {
            'current_tab': 'categories',
            'categories': page_obj,
            'page_obj': page_obj,
            'search_query': search_query,
        }
        return render(request, 'category/CategoriesList.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during load categories: {e}')


@login_required
def add_category(request):
    try:
        if request.method == 'POST':
            name = request.POST.get('name')
            description = request.POST.get('description', '')

            # this check validation requirements to fill the blank fields
            if not name:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'category/AddCategory.html')

            # this checks for a duplicate category name (case-insensitive) so we dont end up with both "Heavy Equipment" and "heavy equipment"
            if Categories.objects.filter(name__iexact=name.strip()).exists():
                messages.error(request, f'Category "{name}" already exists. Please use a different name.')
                return render(request, 'category/AddCategory.html')

            Categories.objects.create(name=name, description=description)
            messages.success(request, 'Category added successfully!')
            return redirect('/category/list')
        else:
            return render(request, 'category/AddCategory.html')
    except Exception as e:
        return HttpResponse(f'Error occurred during add category: {e}')


@login_required
def edit_category(request, categoryId):
    try:
        categoryObj = Categories.objects.get(pk=categoryId)

        # this checks if any equipment under this category has units currently borrowed
        has_active_borrows = BorrowRecords.objects.filter(
            equipment__category=categoryObj, status='borrowed'
        ).exists()
        if has_active_borrows:
            messages.error(request, f'Cannot edit "{categoryObj.name}" — some equipment in this category is currently borrowed. Process the return first.')
            return redirect('/category/list')

        if request.method == 'POST':
            name = request.POST.get('name')
            description = request.POST.get('description', '')

            data = {'category': categoryObj}

            if not name:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'category/EditCategory.html', data)

            # this checks for a duplicate category name, excluding the category being edited
            if Categories.objects.filter(name__iexact=name.strip()).exclude(pk=categoryId).exists():
                messages.error(request, f'Category "{name}" already exists. Please use a different name.')
                return render(request, 'category/EditCategory.html', data)

            categoryObj.name = name
            categoryObj.description = description
            categoryObj.save()
            messages.success(request, 'Category updated successfully!')

        data = {'category': categoryObj}
        return render(request, 'category/EditCategory.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during edit category: {e}')


@login_required
def delete_category(request, categoryId):
    try:
        categoryObj = Categories.objects.get(pk=categoryId)

        # this checks if any equipment still belongs to this category, if so we cant delete
        if categoryObj.equipments.exists():
            messages.error(request, f'Cannot delete "{categoryObj.name}" — it still has equipment assigned. Remove or reassign all equipment first.')
            return redirect('/category/list')

        if request.method == 'POST':
            categoryObj.delete()
            messages.success(request, 'Category deleted successfully!')
            return redirect('/category/list')

        data = {'category': categoryObj}
        return render(request, 'category/DeleteCategory.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during delete category: {e}')


@login_required
def equipment_list(request):
    try:
        # this is for the search and category filter
        search_query = request.GET.get('search', '')
        category_filter = request.GET.get('category', '')

        # sort by equipment_code so the list always reads EQ-001, EQ-002, ... in order,
        # regardless of when each item was added to the system
        equipmentObj = Equipments.objects.select_related('category').all().order_by('equipment_code')

        if search_query:
            equipmentObj = (
                equipmentObj.filter(equipment_name__icontains=search_query) |
                equipmentObj.filter(brand__icontains=search_query) |
                equipmentObj.filter(equipment_code__icontains=search_query)
            )
        if category_filter:
            equipmentObj = equipmentObj.filter(category__category_id=category_filter)

        # this one is for pagination. 15 equipment per page only
        paginator = Paginator(equipmentObj, 15)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        categories = Categories.objects.all()

        data = {
            'current_tab': 'equipment',
            'equipments': page_obj,
            'page_obj': page_obj,
            'categories': categories,
            'search_query': search_query,
            'category_filter': category_filter,
        }
        return render(request, 'equipment/EquipmentList.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during load equipment: {e}')


@login_required
def add_equipment(request):
    try:
        categoryObj = Categories.objects.all()

        if request.method == 'POST':
            equipmentCode = request.POST.get('equipment_code')
            equipmentName = request.POST.get('equipment_name')
            brand = request.POST.get('brand')
            category = request.POST.get('category')
            totalQuantity = request.POST.get('total_quantity')
            description = request.POST.get('description', '')

            data = {'categories': categoryObj}

            # this check validation requirements to fill the blank fields
            if not equipmentCode or not equipmentName or not brand or not category or not totalQuantity:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'equipment/AddEquipment.html', data)

            # this validates the quantity is at least 1 and at most 50 per equipment
            try:
                totalQuantity = int(totalQuantity)
                if totalQuantity < 1:
                    raise ValueError()
            except (ValueError, TypeError):
                messages.error(request, 'Total quantity must be a whole number of 1 or more.')
                return render(request, 'equipment/AddEquipment.html', data)

            # enforce the maximum of 50 units per equipment
            if totalQuantity > 50:
                messages.error(request, 'Total quantity cannot exceed 50 units per equipment.')
                return render(request, 'equipment/AddEquipment.html', data)

            # this checks the duplicate equipment code, if there is a duplicate it wont save and will return a toast error
            if Equipments.objects.filter(equipment_code=equipmentCode).exists():
                messages.error(request, 'Equipment code is already taken. Please choose a different one.')
                return render(request, 'equipment/AddEquipment.html', data)

            newEquipment = Equipments.objects.create(
                equipment_code=equipmentCode,
                equipment_name=equipmentName,
                brand=brand,
                category=Categories.objects.get(pk=category),
                total_quantity=totalQuantity,
                description=description,
            )

            # this is for saving the equipment photo if posted
            photo = request.FILES.get('photo')
            if photo:
                newEquipment.photo = photo
                newEquipment.save()

            messages.success(request, 'Equipment added successfully!')
            return redirect('/equipment/list')
        else:
            data = {'categories': categoryObj}
            return render(request, 'equipment/AddEquipment.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during add equipment: {e}')


@login_required
def edit_equipment(request, equipmentId):
    try:
        equipmentObj = Equipments.objects.select_related('category').get(pk=equipmentId)
        categoryObj = Categories.objects.all()

        # this checks if any units of this equipment are currently borrowed, if so we cant edit
        if equipmentObj.borrowed_quantity > 0:
            messages.error(request, f'Cannot edit "{equipmentObj.equipment_name}" — {equipmentObj.borrowed_quantity} unit(s) are currently borrowed. Process the return first.')
            return redirect('/equipment/list')

        if request.method == 'POST':
            equipmentCode = request.POST.get('equipment_code')
            equipmentName = request.POST.get('equipment_name')
            brand = request.POST.get('brand')
            category = request.POST.get('category')
            totalQuantity = request.POST.get('total_quantity')
            description = request.POST.get('description', '')

            data = {'equipment': equipmentObj, 'categories': categoryObj}

            if not equipmentCode or not equipmentName or not brand or not category or not totalQuantity:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'equipment/EditEquipment.html', data)

            # this validates the quantity is at least 1 and at most 50
            try:
                totalQuantity = int(totalQuantity)
                if totalQuantity < 1:
                    raise ValueError()
            except (ValueError, TypeError):
                messages.error(request, 'Total quantity must be a whole number of 1 or more.')
                return render(request, 'equipment/EditEquipment.html', data)

            # enforce the maximum of 50 units per equipment
            if totalQuantity > 50:
                messages.error(request, 'Total quantity cannot exceed 50 units per equipment.')
                return render(request, 'equipment/EditEquipment.html', data)

            # this checks the duplicate equipment_code excluding the current one
            if Equipments.objects.filter(equipment_code=equipmentCode).exclude(pk=equipmentId).exists():
                messages.error(request, 'Equipment code is already taken. Please choose a different one.')
                return render(request, 'equipment/EditEquipment.html', data)

            equipmentObj.equipment_code = equipmentCode
            equipmentObj.equipment_name = equipmentName
            equipmentObj.brand = brand
            equipmentObj.category = Categories.objects.get(pk=category)
            equipmentObj.total_quantity = totalQuantity
            equipmentObj.description = description

            # this is for changing the equipment photo, leave blank to keep current
            new_photo = request.FILES.get('photo')
            if new_photo:
                equipmentObj.photo = new_photo

            equipmentObj.save()
            messages.success(request, 'Equipment updated successfully!')

        data = {'equipment': equipmentObj, 'categories': categoryObj}
        return render(request, 'equipment/EditEquipment.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during edit equipment: {e}')


@login_required
def delete_equipment(request, equipmentId):
    try:
        equipmentObj = Equipments.objects.get(pk=equipmentId)

        # this checks if any units are currently borrowed, if so we cant delete
        if equipmentObj.borrowed_quantity > 0:
            messages.error(request, f'Cannot delete "{equipmentObj.equipment_name}" — {equipmentObj.borrowed_quantity} unit(s) are currently borrowed. Process the return first.')
            return redirect('/equipment/list')

        if request.method == 'POST':
            equipmentObj.delete()
            messages.success(request, 'Equipment deleted successfully!')
            return redirect('/equipment/list')

        data = {'equipment': equipmentObj}
        return render(request, 'equipment/DeleteEquipment.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during delete equipment: {e}')


@login_required
def borrow_form(request):
    try:
        from datetime import date, timedelta

        # build a list of categories with their available equipment for the grouped dropdown.
        # only categories that have at least one available equipment make it into this list.
        categories_with_equipment = []
        max_available = 1  # used to set the quantity input's max attribute
        for cat in Categories.objects.all():
            available_eqs = [eq for eq in cat.equipments.all() if eq.available_quantity > 0]
            if available_eqs:
                categories_with_equipment.append({
                    'name': cat.name,
                    'equipments': available_eqs,
                })
                # track the highest available count so the quantity input will show remaining available
                for eq in available_eqs:
                    if eq.available_quantity > max_available:
                        max_available = eq.available_quantity

        borrowers = Borrowers.objects.filter(active=True)
        # this lists every equipment that is currently borrowed 
        borrow_records = BorrowRecords.objects.filter(status='borrowed').select_related('equipment', 'borrower').order_by('-borrow_date')

        # today's date used as the minimum for the return date picker.
        # allowing today enables same-day loans (borrow and return within the same day),
        # while the min attribute still blocks selecting any date in the past.
        today_date = date.today().isoformat()

        data = {
            'current_tab': 'borrow',
            'categories_with_equipment': categories_with_equipment,
            'borrowers': borrowers,
            'borrow_records': borrow_records,
            'today_date': today_date,
            'max_available': max_available,
        }
        return render(request, 'borrow/BorrowForm.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during load borrow form: {e}')


@login_required
def save_borrow(request):
    try:
        if request.method == 'POST':
            equipmentId = request.POST.get('equipment_id')
            # the borrower comes from a searchable datalist input that submits "Name | reference_id".
            borrowerInput = request.POST.get('borrower_input', '').strip()
            quantity = request.POST.get('quantity')
            expectedReturn = request.POST.get('expected_return')
            notes = request.POST.get('notes', '')

            # this check validation requirements to fill the blank fields
            if not equipmentId or not borrowerInput or not expectedReturn or not quantity:
                messages.error(request, 'Please complete all required fields before submitting.')
                return redirect('/borrow')

            # the user MUST pick a valid option from the dropdown, only accept names that are in the registry
            if ' | ' not in borrowerInput:
                messages.error(request, 'Please select a borrower from the list (start typing to search).')
                return redirect('/borrow')

            try:
                _, reference_id = borrowerInput.rsplit(' | ', 1)
                borrowerObj = Borrowers.objects.get(reference_id=reference_id.strip())
            except Borrowers.DoesNotExist:
                messages.error(request, 'Selected borrower not found. Please pick one from the list.')
                return redirect('/borrow')

            # this validates the quantity is a whole number greater equal to 1
            try:
                quantity = int(quantity)
                if quantity < 1:
                    raise ValueError()
            except (ValueError, TypeError):
                messages.error(request, 'Quantity must be a whole number of 1 or more.')
                return redirect('/borrow')

            equipmentObj = Equipments.objects.get(pk=equipmentId)

            # block any borrow if nothing is on the shelf
            if equipmentObj.available_quantity <= 0:
                messages.error(request, f'"{equipmentObj.equipment_name}" has 0 units available — cannot be borrowed right now.')
                return redirect('/borrow')

            # this checks if there are enough units available
            if quantity > equipmentObj.available_quantity:
                messages.error(request, f'Only {equipmentObj.available_quantity} unit(s) of "{equipmentObj.equipment_name}" are available — cannot borrow {quantity}.')
                return redirect('/borrow')

            # this solves the category name at borrow time, used for the snapshot
            category_name = equipmentObj.category.name if equipmentObj.category else ''

            BorrowRecords.objects.create(
                equipment=equipmentObj,
                borrower=borrowerObj,
                quantity=quantity,
                expected_return=expectedReturn,
                notes=notes,
                status='borrowed',

                # frozen at creation so deleting borrower and equipment never erases this data from historical records.
                borrower_name_snapshot=borrowerObj.borrower_name,
                borrower_contact_snapshot=borrowerObj.borrower_contact,
                equipment_name_snapshot=equipmentObj.equipment_name,
                equipment_code_snapshot=equipmentObj.equipment_code,
                category_name_snapshot=category_name,
            )
            # Availability is calculated live from total_quantity - borrowed_quantity.

            messages.success(request, f'Borrow request confirmed — {quantity} unit(s) issued.')
        return redirect('/borrow')
    except Exception as e:
        return HttpResponse(f'Error occurred during save borrow: {e}')


@login_required
def returns_list(request):
    try:
        # all the equipment still on borrow shows at the top of the page and pending returns
        borrow_records = BorrowRecords.objects.filter(status='borrowed').order_by('-borrow_date')

        # Returned history with search + category dropdown filter + pagination
        return_search = request.GET.get('return_search', '').strip()
        category_filter = request.GET.get('return_category', '').strip()
        returned_qs = BorrowRecords.objects.filter(status='returned').order_by('-actual_return', '-created_at')

        # text search covers borrower, equipment name, and equipment code
        if return_search:
            returned_qs = (
                returned_qs.filter(borrower_name_snapshot__icontains=return_search) |
                returned_qs.filter(equipment_name_snapshot__icontains=return_search) |
                returned_qs.filter(equipment_code_snapshot__icontains=return_search)
            )

        # category is a separate dropdown filter (matches the category snapshot exactly)
        if category_filter:
            returned_qs = returned_qs.filter(category_name_snapshot=category_filter)

        # build the dropdown options from category names that actually appear in returned records
        return_categories = (
            BorrowRecords.objects.filter(status='returned')
            .exclude(category_name_snapshot='')
            .values_list('category_name_snapshot', flat=True)
            .distinct()
            .order_by('category_name_snapshot')
        )

        # paginate 10 per page
        returned_paginator = Paginator(returned_qs, 10)
        returned_page_number = request.GET.get('return_page')
        returned_page_obj = returned_paginator.get_page(returned_page_number)

        data = {
            'current_tab': 'returns',
            'borrow_records': borrow_records,
            'returned_records': returned_page_obj,
            'returned_page_obj': returned_page_obj,
            'return_search': return_search,
            'category_filter': category_filter,
            'return_categories': return_categories,
        }
        return render(request, 'returns/ReturnsList.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during load returns: {e}')


@login_required
def process_return(request, recordId):
    try:
        recordObj = BorrowRecords.objects.get(pk=recordId)
        # mark this record as returned, stamp todays date
        recordObj.status = 'returned'
        recordObj.actual_return = timezone.localdate()
        recordObj.save()
        messages.success(request, f'Return accepted — {recordObj.quantity} unit(s) back on the shelf.')
        return redirect('/returns')
    except Exception as e:
        return HttpResponse(f'Error occurred during process return: {e}')


@login_required
def get_equipment_by_category(request):
    # this is the JSON endpoint used by the borrow page to populate equipment after a category is picked
    try:
        category_id = request.GET.get('category_id')
        equipment_qs = Equipments.objects.filter(category__category_id=category_id)

        # we have to compute available quantity per row
        result = []
        for eq in equipment_qs:
            avail = eq.available_quantity
            if avail > 0:
                result.append({
                    'equipment_id': eq.equipment_id,
                    'equipment_name': eq.equipment_name,
                    'brand': eq.brand,
                    'equipment_code': eq.equipment_code,
                    'available_quantity': avail,
                })
        return JsonResponse(result, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
