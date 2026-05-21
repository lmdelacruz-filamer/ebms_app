from django.db import models

# Create your models here.

class Categories(models.Model):
    class Meta:
        db_table = 'tbl_categories'
        verbose_name_plural = 'Categories'

    category_id = models.BigAutoField(primary_key=True, blank=False) # category_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY
    name = models.CharField(max_length=200, blank=False) # name VARCHAR(200) NOT NULL
    description = models.TextField(blank=True) # description TEXT DEFAULT NULL
    created_at = models.DateTimeField(auto_now_add=True) # created at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at = models.DateTimeField(auto_now=True) # updated at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

    def __str__(self):
        return self.name

    # sums up the total_quantity of every equipment in this category.
    # SQL equivalent: SELECT SUM(total_quantity) FROM tbl_equipments WHERE category_id = ?
    @property
    def total_units(self):
        from django.db.models import Sum
        result = self.equipments.aggregate(total=Sum('total_quantity'))['total']
        return result or 0


class Equipments(models.Model):
    class Meta:
        db_table = 'tbl_equipments'

    equipment_id = models.BigAutoField(primary_key=True, blank=False) # equipment_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY
    equipment_code = models.CharField(max_length=200, blank=False, unique=True) # equipment_code VARCHAR(200) NOT NULL UNIQUE (e.g. EQ-001)
    equipment_name = models.CharField(max_length=200, blank=False) # equipment_name VARCHAR(200) NOT NULL
    brand = models.CharField(max_length=200, blank=False) # brand VARCHAR(200) NOT NULL
    category = models.ForeignKey(Categories, on_delete=models.SET_NULL, null=True, related_name='equipments') # category_id BIGINT // FOREIGN KEY (category_id) REFERENCES tbl_categories(category_id) ON DELETE SET NULL
    photo = models.ImageField(upload_to='equipment_photos/', blank=True, null=True) # photo VARCHAR(255) DEFAULT NULL
    total_quantity = models.PositiveIntegerField(default=1) # total_quantity INT UNSIGNED NOT NULL DEFAULT 1 (how many physical units we own of this item)
    description = models.TextField(blank=True) # description TEXT DEFAULT NULL
    created_at = models.DateTimeField(auto_now_add=True) # created at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at = models.DateTimeField(auto_now=True) # updated at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

    def __str__(self):
        return self.equipment_name

    # these properties compute live availability based on outstanding borrow records.
    # SQL equivalent: SELECT SUM(quantity) FROM tbl_borrow_records WHERE equipment_id = ? AND status = 'borrowed'
    @property
    def borrowed_quantity(self):
        from django.db.models import Sum
        result = self.borrow_records.filter(status='borrowed').aggregate(total=Sum('quantity'))['total']
        return result or 0

    @property
    def available_quantity(self):
        # how many units are on the shelf right now
        return self.total_quantity - self.borrowed_quantity

    @property
    def is_borrowable(self):
        # convenience flag for guards / templates
        return self.available_quantity > 0


class Borrowers(models.Model):
    class Meta:
        db_table = 'tbl_borrowers'

    borrower_id = models.BigAutoField(primary_key=True, blank=False) # borrower_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY
    reference_id = models.CharField(max_length=200, blank=False) # reference_id VARCHAR(200) NOT NULL (employee/student ID)
    borrower_name = models.CharField(max_length=200, blank=False) # borrower_name VARCHAR(200) NOT NULL
    borrower_contact = models.CharField(max_length=200, blank=False) # borrower_contact VARCHAR(200) NOT NULL
    borrower_address = models.TextField(blank=False) # borrower_address TEXT NOT NULL
    active = models.BooleanField(default=True) # active TINYINT(1) NOT NULL DEFAULT 1
    created_at = models.DateTimeField(auto_now_add=True) # created at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at = models.DateTimeField(auto_now=True) # updated at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

    def __str__(self):
        return self.borrower_name


class BorrowRecords(models.Model):
    class Meta:
        db_table = 'tbl_borrow_records'

    # this is the list of allowed status values for a borrow record
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
    ]

    record_id = models.BigAutoField(primary_key=True, blank=False) # record_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY

    # how many units of the equipment this record covers (pooled inventory)
    quantity = models.PositiveIntegerField(default=1) # quantity INT UNSIGNED NOT NULL DEFAULT 1

    # Live FK links — SET_NULL so the record row is never erased if the equipment
    # or borrower is later deleted. The snapshot columns below preserve history.
    equipment = models.ForeignKey(Equipments, on_delete=models.SET_NULL, null=True, blank=True, related_name='borrow_records') # equipment_id BIGINT // FOREIGN KEY (equipment_id) REFERENCES tbl_equipments(equipment_id) ON DELETE SET NULL
    borrower = models.ForeignKey(Borrowers, on_delete=models.SET_NULL, null=True, blank=True, related_name='borrow_records') # borrower_id BIGINT // FOREIGN KEY (borrower_id) REFERENCES tbl_borrowers(borrower_id) ON DELETE SET NULL

    borrower_name_snapshot = models.CharField(max_length=200, blank=True, default='') # borrower_name_snapshot VARCHAR(200) NOT NULL DEFAULT ''
    borrower_contact_snapshot = models.CharField(max_length=200, blank=True, default='') # borrower_contact_snapshot VARCHAR(200) NOT NULL DEFAULT ''
    equipment_name_snapshot = models.CharField(max_length=200, blank=True, default='') # equipment_name_snapshot VARCHAR(200) NOT NULL DEFAULT ''
    equipment_code_snapshot = models.CharField(max_length=200, blank=True, default='') # equipment_code_snapshot VARCHAR(200) NOT NULL DEFAULT ''
    category_name_snapshot = models.CharField(max_length=200, blank=True, default='') # category_name_snapshot VARCHAR(200) NOT NULL DEFAULT ''

    borrow_date = models.DateField(auto_now_add=True) # borrow_date DATE NOT NULL DEFAULT CURRENT_DATE
    expected_return = models.DateField(blank=False) # expected_return DATE NOT NULL
    actual_return = models.DateField(null=True, blank=True) # actual_return DATE DEFAULT NULL
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed') # status VARCHAR(20) NOT NULL DEFAULT 'borrowed'
    notes = models.TextField(blank=True) # notes TEXT DEFAULT NULL
    created_at = models.DateTimeField(auto_now_add=True) # created at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    def __str__(self):
        b = self.borrower_name_snapshot or (self.borrower.borrower_name if self.borrower else '[Deleted Borrower]')
        e = self.equipment_name_snapshot or (self.equipment.equipment_name if self.equipment else '[Deleted Equipment]')
        return f'{b} -> {e}'

    # these "display_" properties fall back to the live FK if available,
    # otherwise to the snapshot, otherwise to a placeholder. used in templates.
    @property
    def display_borrower_name(self):
        return self.borrower_name_snapshot or (
            self.borrower.borrower_name if self.borrower else '[Deleted Borrower]'
        )

    @property
    def display_borrower_contact(self):
        return self.borrower_contact_snapshot or (
            self.borrower.borrower_contact if self.borrower else '—'
        )

    @property
    def display_equipment_name(self):
        return self.equipment_name_snapshot or (
            self.equipment.equipment_name if self.equipment else '[Deleted Equipment]'
        )

    @property
    def display_equipment_code(self):
        return self.equipment_code_snapshot or (
            self.equipment.equipment_code if self.equipment else '—'
        )

    @property
    def display_category_name(self):
        return self.category_name_snapshot or (
            self.equipment.category.name if self.equipment and self.equipment.category else '—'
        )
