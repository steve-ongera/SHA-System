from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


# ============= USER MANAGEMENT & ROLES =============

class User(AbstractUser):
    """Extended user model with role-based access"""
    ROLE_CHOICES = [
        ('ADMIN', 'System Administrator'),
        ('SHA_OFFICER', 'SHA Officer'),
        ('EMPLOYER', 'Employer'),
        ('PROVIDER', 'Healthcare Provider'),
        ('MEMBER', 'Member/Contributor'),
        ('CLAIMS_OFFICER', 'Claims Officer'),
        ('FINANCE_OFFICER', 'Finance Officer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        

# ============= MEMBER & REGISTRATION =============

class Member(models.Model):
    """Core member/beneficiary information"""
    MEMBER_TYPE_CHOICES = [
        ('PRINCIPAL', 'Principal Member'),
        ('DEPENDENT', 'Dependent'),
    ]
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('EMPLOYED', 'Employed'),
        ('SELF_EMPLOYED', 'Self Employed'),
        ('UNEMPLOYED', 'Unemployed'),
        ('STUDENT', 'Student'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Personal Information
    national_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    other_names = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    
    # SHA Details
    sha_number = models.CharField(max_length=20, unique=True, blank=True)
    member_type = models.CharField(max_length=20, choices=MEMBER_TYPE_CHOICES)
    principal_member = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='dependents')
    
    # Employment
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES)
    employer = models.ForeignKey('Employer', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Registration
    registration_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_subsidized = models.BooleanField(default=False)  # Government subsidy
    
    # Address
    county = models.CharField(max_length=100)
    sub_county = models.CharField(max_length=100)
    ward = models.CharField(max_length=100)
    postal_address = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'members'
        indexes = [
            models.Index(fields=['national_id']),
            models.Index(fields=['sha_number']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.sha_number}"


# ============= EMPLOYER MANAGEMENT =============

class Employer(models.Model):
    """Employer/Organization information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Organization Details
    employer_code = models.CharField(max_length=20, unique=True)
    company_name = models.CharField(max_length=200)
    kra_pin = models.CharField(max_length=20, unique=True)
    business_registration_number = models.CharField(max_length=50)
    
    # Contact Information
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    postal_address = models.TextField()
    physical_address = models.TextField()
    
    # Bank Details for remittance
    bank_name = models.CharField(max_length=100)
    bank_branch = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    
    is_active = models.BooleanField(default=True)
    registration_date = models.DateField(auto_now_add=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employers'
    
    def __str__(self):
        return f"{self.company_name} - {self.employer_code}"


# ============= CONTRIBUTION MANAGEMENT =============

class Contribution(models.Model):
    """Monthly contributions from members/employers"""
    CONTRIBUTION_METHOD_CHOICES = [
        ('SALARY_DEDUCTION', 'Salary Deduction'),
        ('MPESA', 'M-Pesa'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('USSD', 'USSD Payment'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REVERSED', 'Reversed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='contributions')
    employer = models.ForeignKey(Employer, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contribution Details
    contribution_month = models.DateField()  # Month for which contribution is made
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    contribution_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('300.00'))])
    contribution_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.75'))  # Percentage
    
    # Payment Details
    payment_method = models.CharField(max_length=30, choices=CONTRIBUTION_METHOD_CHOICES)
    transaction_reference = models.CharField(max_length=100, unique=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Audit
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contributions'
        unique_together = ['member', 'contribution_month']
        indexes = [
            models.Index(fields=['contribution_month', 'status']),
        ]
    
    def __str__(self):
        return f"{self.member.sha_number} - {self.contribution_month} - KES {self.contribution_amount}"


# ============= HEALTHCARE PROVIDER MANAGEMENT =============

class HealthcareProvider(models.Model):
    """Healthcare facilities/hospitals"""
    FACILITY_LEVEL_CHOICES = [
        ('LEVEL_1', 'Level 1 - Community'),
        ('LEVEL_2', 'Level 2 - Dispensary'),
        ('LEVEL_3', 'Level 3 - Health Centre'),
        ('LEVEL_4', 'Level 4 - Sub-County Hospital'),
        ('LEVEL_5', 'Level 5 - County Referral'),
        ('LEVEL_6', 'Level 6 - National Referral'),
    ]
    
    FACILITY_TYPE_CHOICES = [
        ('PUBLIC', 'Public'),
        ('PRIVATE', 'Private'),
        ('FAITH_BASED', 'Faith-Based'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Facility Details
    facility_code = models.CharField(max_length=20, unique=True)
    facility_name = models.CharField(max_length=200)
    facility_level = models.CharField(max_length=20, choices=FACILITY_LEVEL_CHOICES)
    facility_type = models.CharField(max_length=20, choices=FACILITY_TYPE_CHOICES)
    
    # Registration
    license_number = models.CharField(max_length=50, unique=True)
    kmpdb_number = models.CharField(max_length=50, blank=True)  # Kenya Medical Practitioners Board
    
    # Contact
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    county = models.CharField(max_length=100)
    sub_county = models.CharField(max_length=100)
    physical_address = models.TextField()
    
    # Bank Details
    bank_name = models.CharField(max_length=100)
    bank_branch = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    
    # Contract
    contract_start_date = models.DateField()
    contract_end_date = models.DateField(null=True, blank=True)
    is_contracted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'healthcare_providers'
    
    def __str__(self):
        return f"{self.facility_name} - {self.facility_code}"


# ============= BENEFIT PACKAGES =============

class BenefitPackage(models.Model):
    """SHA benefit packages (SHIF, PHCF, ECCIF)"""
    PACKAGE_TYPE_CHOICES = [
        ('SHIF', 'Social Health Insurance Fund'),
        ('PHCF', 'Primary Healthcare Fund'),
        ('ECCIF', 'Emergency, Chronic & Critical Illness Fund'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    package_code = models.CharField(max_length=20, unique=True)
    package_name = models.CharField(max_length=200)
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPE_CHOICES)
    description = models.TextField()
    
    # Coverage limits
    annual_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    per_illness_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Eligibility
    applicable_facility_levels = models.JSONField(default=list)  # ['LEVEL_4', 'LEVEL_5', 'LEVEL_6']
    
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'benefit_packages'
    
    def __str__(self):
        return f"{self.package_name} ({self.package_type})"


class BenefitService(models.Model):
    """Individual services covered under benefit packages"""
    SERVICE_CATEGORY_CHOICES = [
        ('OUTPATIENT', 'Outpatient Services'),
        ('INPATIENT', 'Inpatient Services'),
        ('MATERNITY', 'Maternity Services'),
        ('SURGERY', 'Surgical Procedures'),
        ('RADIOLOGY', 'Radiology & Imaging'),
        ('LABORATORY', 'Laboratory Services'),
        ('DENTAL', 'Dental Services'),
        ('DIALYSIS', 'Dialysis'),
        ('CANCER_TREATMENT', 'Cancer Treatment'),
        ('CARDIOLOGY', 'Cardiology'),
        ('EMERGENCY', 'Emergency Services'),
        ('CHRONIC_ILLNESS', 'Chronic Illness Management'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    benefit_package = models.ForeignKey(BenefitPackage, on_delete=models.CASCADE, related_name='services')
    
    service_code = models.CharField(max_length=20, unique=True)
    service_name = models.CharField(max_length=200)
    service_category = models.CharField(max_length=30, choices=SERVICE_CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    
    # Tariff
    standard_tariff = models.DecimalField(max_digits=10, decimal_places=2)
    copayment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    copayment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Limits
    annual_frequency_limit = models.IntegerField(null=True, blank=True)  # e.g., 2 times per year
    per_visit_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    requires_preauthorization = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'benefit_services'
    
    def __str__(self):
        return f"{self.service_name} - KES {self.standard_tariff}"


# ============= PRE-AUTHORIZATION =============

class PreAuthorization(models.Model):
    """Pre-authorization requests for certain procedures"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    authorization_number = models.CharField(max_length=20, unique=True)
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='preauthorizations')
    healthcare_provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE)
    benefit_service = models.ForeignKey(BenefitService, on_delete=models.CASCADE)
    
    # Request Details
    diagnosis = models.TextField()
    procedure_description = models.TextField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    requested_date = models.DateField()
    planned_procedure_date = models.DateField()
    
    # Supporting Documents
    supporting_documents = models.JSONField(default=list)  # List of file paths/URLs
    
    # Approval Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_preauths')
    
    rejection_reason = models.TextField(blank=True)
    valid_until = models.DateField(null=True, blank=True)
    
    # Audit
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='submitted_preauths')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'preauthorizations'
        indexes = [
            models.Index(fields=['status', 'planned_procedure_date']),
        ]
    
    def __str__(self):
        return f"{self.authorization_number} - {self.member.sha_number}"


# ============= CLAIMS MANAGEMENT =============

class Claim(models.Model):
    """Claims submitted by healthcare providers"""
    CLAIM_TYPE_CHOICES = [
        ('OUTPATIENT', 'Outpatient'),
        ('INPATIENT', 'Inpatient'),
        ('EMERGENCY', 'Emergency'),
    ]
    
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('QUERIED', 'Queried'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Paid'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim_number = models.CharField(max_length=20, unique=True)
    
    # Parties
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='claims')
    healthcare_provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE, related_name='claims')
    benefit_package = models.ForeignKey(BenefitPackage, on_delete=models.CASCADE)
    
    # Visit Details
    claim_type = models.CharField(max_length=20, choices=CLAIM_TYPE_CHOICES)
    visit_date = models.DateField()
    admission_date = models.DateField(null=True, blank=True)
    discharge_date = models.DateField(null=True, blank=True)
    
    # Clinical Information
    diagnosis = models.TextField()
    icd_code = models.CharField(max_length=20, blank=True)  # ICD-10 codes
    
    # Financial
    claimed_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rejected_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    copayment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    submission_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    rejection_reason = models.TextField(blank=True)
    query_comments = models.TextField(blank=True)
    
    # Pre-authorization reference
    preauthorization = models.ForeignKey(PreAuthorization, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Documents
    supporting_documents = models.JSONField(default=list)
    
    # Audit
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_claims')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_claims')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'claims'
        indexes = [
            models.Index(fields=['status', 'submission_date']),
            models.Index(fields=['healthcare_provider', 'status']),
        ]
    
    def __str__(self):
        return f"{self.claim_number} - {self.member.sha_number} - KES {self.claimed_amount}"


class ClaimItem(models.Model):
    """Individual services/items within a claim"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='claim_items')
    benefit_service = models.ForeignKey(BenefitService, on_delete=models.CASCADE)
    
    service_date = models.DateField()
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    approved_quantity = models.IntegerField(null=True, blank=True)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'claim_items'
    
    def __str__(self):
        return f"{self.claim.claim_number} - {self.benefit_service.service_name}"


# ============= PAYMENTS =============

class Payment(models.Model):
    """Payments made to healthcare providers"""
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_reference = models.CharField(max_length=50, unique=True)
    
    healthcare_provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE, related_name='payments')
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='payments')
    
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50, default='Bank Transfer')
    
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    
    # Bank details used
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    transaction_reference = models.CharField(max_length=100, blank=True)
    
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        indexes = [
            models.Index(fields=['payment_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.payment_reference} - {self.healthcare_provider.facility_name} - KES {self.payment_amount}"


# ============= ELIGIBILITY & VERIFICATION =============

class EligibilityCheck(models.Model):
    """Track eligibility verifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='eligibility_checks')
    healthcare_provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE)
    
    check_date = models.DateTimeField(auto_now_add=True)
    is_eligible = models.BooleanField()
    
    # Reasons for ineligibility
    ineligibility_reason = models.TextField(blank=True)
    
    # Contribution status
    contributions_up_to_date = models.BooleanField()
    last_contribution_date = models.DateField(null=True, blank=True)
    
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'eligibility_checks'
        indexes = [
            models.Index(fields=['member', 'check_date']),
        ]
    
    def __str__(self):
        return f"{self.member.sha_number} - {'Eligible' if self.is_eligible else 'Not Eligible'}"


# ============= AUDIT & COMPLIANCE =============

class AuditLog(models.Model):
    """System audit trail"""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('PAYMENT', 'Payment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=100)
    
    changes = models.JSONField(default=dict)  # Before and after values
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} - {self.timestamp}"


# ============= NOTIFICATIONS =============

class Notification(models.Model):
    """User notifications"""
    NOTIFICATION_TYPE_CHOICES = [
        ('CONTRIBUTION_DUE', 'Contribution Due'),
        ('CONTRIBUTION_RECEIVED', 'Contribution Received'),
        ('CLAIM_SUBMITTED', 'Claim Submitted'),
        ('CLAIM_APPROVED', 'Claim Approved'),
        ('CLAIM_REJECTED', 'Claim Rejected'),
        ('PAYMENT_MADE', 'Payment Made'),
        ('PREAUTH_APPROVED', 'Pre-authorization Approved'),
        ('PREAUTH_REJECTED', 'Pre-authorization Rejected'),
        ('SYSTEM_ALERT', 'System Alert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Reference to related object
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.title}"


# ============= REPORTS & ANALYTICS =============

class Report(models.Model):
    """Generated reports"""
    REPORT_TYPE_CHOICES = [
        ('CONTRIBUTION_SUMMARY', 'Contribution Summary'),
        ('CLAIMS_REPORT', 'Claims Report'),
        ('PAYMENT_REPORT', 'Payment Report'),
        ('UTILIZATION_REPORT', 'Utilization Report'),
        ('PROVIDER_PERFORMANCE', 'Provider Performance'),
        ('MEMBER_ENROLLMENT', 'Member Enrollment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    report_name = models.CharField(max_length=200)
    
    # Period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Filters applied
    filters = models.JSONField(default=dict)
    
    # File
    file_path = models.CharField(max_length=500, blank=True)
    file_format = models.CharField(max_length=10, choices=[('PDF', 'PDF'), ('EXCEL', 'Excel'), ('CSV', 'CSV')])
    
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reports'
        indexes = [
            models.Index(fields=['report_type', 'generated_at']),
        ]
    
    def __str__(self):
        return f"{self.report_name} - {self.start_date} to {self.end_date}"