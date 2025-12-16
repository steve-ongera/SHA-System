from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, Member, Employer, Contribution, HealthcareProvider,
    BenefitPackage, BenefitService, PreAuthorization, Claim,
    ClaimItem, Payment, EligibilityCheck, AuditLog, Notification, Report
)


# ============= CUSTOM FILTERS =============

class ContributionStatusFilter(admin.SimpleListFilter):
    title = 'Contribution Status'
    parameter_name = 'contribution_status'

    def lookups(self, request, model_admin):
        return (
            ('up_to_date', 'Up to Date'),
            ('pending', 'Pending'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'up_to_date':
            return queryset.filter(contributions__status='COMPLETED')
        if self.value() == 'pending':
            return queryset.filter(contributions__status='PENDING')


class ActiveMemberFilter(admin.SimpleListFilter):
    title = 'Member Status'
    parameter_name = 'member_status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_active=True)
        if self.value() == 'inactive':
            return queryset.filter(is_active=False)


# ============= USER ADMIN =============

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'phone_number', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'phone_number', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('SHA Information', {
            'fields': ('role', 'phone_number', 'is_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('SHA Information', {
            'fields': ('role', 'phone_number', 'is_verified')
        }),
    )
    
    list_per_page = 50
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(request.user, 'role') and request.user.role == 'SHA_OFFICER':
            return qs
        return qs


# ============= MEMBER ADMIN =============

class DependentInline(admin.TabularInline):
    model = Member
    fk_name = 'principal_member'
    extra = 0
    fields = ('first_name', 'last_name', 'national_id', 'date_of_birth', 'gender', 'is_active')
    readonly_fields = ('first_name', 'last_name', 'national_id')
    can_delete = False
    show_change_link = True


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        'sha_number', 'full_name', 'national_id', 'member_type', 
        'employment_status', 'employer_link', 'is_active', 'registration_date'
    )
    list_filter = ('member_type', 'employment_status', 'is_active', ActiveMemberFilter, 'county')
    search_fields = ('sha_number', 'national_id', 'first_name', 'last_name', 'email', 'phone_number')
    readonly_fields = ('sha_number', 'registration_date', 'created_at', 'updated_at')
    date_hierarchy = 'registration_date'
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'sha_number', 'national_id', 'first_name', 'last_name', 'other_names',
                'date_of_birth', 'gender', 'email', 'phone_number'
            )
        }),
        ('SHA Details', {
            'fields': ('member_type', 'principal_member', 'is_active', 'is_subsidized')
        }),
        ('Employment', {
            'fields': ('employment_status', 'employer')
        }),
        ('Address', {
            'fields': ('county', 'sub_county', 'ward', 'postal_address')
        }),
        ('System', {
            'fields': ('user', 'registration_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [DependentInline]
    list_per_page = 50
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Full Name'
    
    def employer_link(self, obj):
        if obj.employer:
            url = reverse('admin:sha_system_employer_change', args=[obj.employer.id])
            return format_html('<a href="{}">{}</a>', url, obj.employer.company_name)
        return '-'
    employer_link.short_description = 'Employer'
    
    def save_model(self, request, obj, form, change):
        if not obj.sha_number:
            # Generate SHA number (format: SHA/YYYY/XXXXXX)
            import datetime
            year = datetime.datetime.now().year
            last_member = Member.objects.filter(
                sha_number__startswith=f'SHA/{year}/'
            ).order_by('-sha_number').first()
            
            if last_member:
                last_number = int(last_member.sha_number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            obj.sha_number = f'SHA/{year}/{new_number:06d}'
        
        super().save_model(request, obj, form, change)


# ============= EMPLOYER ADMIN =============

@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = (
        'employer_code', 'company_name', 'kra_pin', 'phone_number', 
        'email', 'employee_count', 'is_active', 'registration_date'
    )
    list_filter = ('is_active', 'registration_date')
    search_fields = ('employer_code', 'company_name', 'kra_pin', 'email', 'phone_number')
    readonly_fields = ('employer_code', 'registration_date', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Organization Details', {
            'fields': ('employer_code', 'company_name', 'kra_pin', 'business_registration_number')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number', 'postal_address', 'physical_address')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'bank_branch', 'account_number')
        }),
        ('Status', {
            'fields': ('is_active', 'registration_date')
        }),
        ('System', {
            'fields': ('user', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    
    def employee_count(self, obj):
        count = Member.objects.filter(employer=obj, is_active=True).count()
        return format_html('<strong>{}</strong>', count)
    employee_count.short_description = 'Active Employees'
    
    def save_model(self, request, obj, form, change):
        if not obj.employer_code:
            # Generate employer code (format: EMP/XXXXXX)
            last_employer = Employer.objects.order_by('-employer_code').first()
            if last_employer and last_employer.employer_code.startswith('EMP/'):
                last_number = int(last_employer.employer_code.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            obj.employer_code = f'EMP/{new_number:06d}'
        
        super().save_model(request, obj, form, change)


# ============= CONTRIBUTION ADMIN =============

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_reference', 'member_link', 'contribution_month', 
        'contribution_amount', 'payment_method', 'status', 'payment_date'
    )
    list_filter = ('status', 'payment_method', 'contribution_month')
    search_fields = ('transaction_reference', 'member__sha_number', 'member__first_name', 'member__last_name')
    readonly_fields = ('payment_date', 'created_at', 'updated_at')
    date_hierarchy = 'contribution_month'
    
    fieldsets = (
        ('Contribution Details', {
            'fields': ('member', 'employer', 'contribution_month')
        }),
        ('Amount Details', {
            'fields': ('gross_salary', 'contribution_rate', 'contribution_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'transaction_reference', 'status', 'payment_date')
        }),
        ('Audit', {
            'fields': ('submitted_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def member_link(self, obj):
        url = reverse('admin:sha_system_member_change', args=[obj.member.id])
        return format_html('<a href="{}">{}</a>', url, obj.member.sha_number)
    member_link.short_description = 'Member'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f'{updated} contribution(s) marked as completed.')
    mark_as_completed.short_description = 'Mark as Completed'
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='FAILED')
        self.message_user(request, f'{updated} contribution(s) marked as failed.')
    mark_as_failed.short_description = 'Mark as Failed'


# ============= HEALTHCARE PROVIDER ADMIN =============

@admin.register(HealthcareProvider)
class HealthcareProviderAdmin(admin.ModelAdmin):
    list_display = (
        'facility_code', 'facility_name', 'facility_level', 'facility_type',
        'county', 'is_contracted', 'is_active', 'contract_start_date'
    )
    list_filter = ('facility_level', 'facility_type', 'is_contracted', 'is_active', 'county')
    search_fields = ('facility_code', 'facility_name', 'license_number', 'email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Facility Details', {
            'fields': ('facility_code', 'facility_name', 'facility_level', 'facility_type')
        }),
        ('Registration', {
            'fields': ('license_number', 'kmpdb_number')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number', 'county', 'sub_county', 'physical_address')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'bank_branch', 'account_number')
        }),
        ('Contract', {
            'fields': ('contract_start_date', 'contract_end_date', 'is_contracted', 'is_active')
        }),
        ('System', {
            'fields': ('user', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    
    def save_model(self, request, obj, form, change):
        if not obj.facility_code:
            # Generate facility code (format: FAC/XXXXXX)
            last_facility = HealthcareProvider.objects.order_by('-facility_code').first()
            if last_facility and last_facility.facility_code.startswith('FAC/'):
                last_number = int(last_facility.facility_code.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            obj.facility_code = f'FAC/{new_number:06d}'
        
        super().save_model(request, obj, form, change)


# ============= BENEFIT PACKAGE & SERVICES ADMIN =============

class BenefitServiceInline(admin.TabularInline):
    model = BenefitService
    extra = 1
    fields = ('service_code', 'service_name', 'service_category', 'standard_tariff', 'requires_preauthorization')


@admin.register(BenefitPackage)
class BenefitPackageAdmin(admin.ModelAdmin):
    list_display = (
        'package_code', 'package_name', 'package_type', 'annual_limit',
        'is_active', 'effective_date', 'service_count'
    )
    list_filter = ('package_type', 'is_active')
    search_fields = ('package_code', 'package_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Package Details', {
            'fields': ('package_code', 'package_name', 'package_type', 'description')
        }),
        ('Coverage Limits', {
            'fields': ('annual_limit', 'per_illness_limit', 'applicable_facility_levels')
        }),
        ('Validity', {
            'fields': ('is_active', 'effective_date', 'end_date')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [BenefitServiceInline]
    list_per_page = 50
    
    def service_count(self, obj):
        count = obj.services.count()
        return format_html('<strong>{}</strong>', count)
    service_count.short_description = 'Services'


@admin.register(BenefitService)
class BenefitServiceAdmin(admin.ModelAdmin):
    list_display = (
        'service_code', 'service_name', 'service_category', 'benefit_package',
        'standard_tariff', 'requires_preauthorization', 'is_active'
    )
    list_filter = ('service_category', 'requires_preauthorization', 'is_active', 'benefit_package')
    search_fields = ('service_code', 'service_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Service Details', {
            'fields': ('benefit_package', 'service_code', 'service_name', 'service_category', 'description')
        }),
        ('Tariff', {
            'fields': ('standard_tariff', 'copayment_amount', 'copayment_percentage')
        }),
        ('Limits', {
            'fields': ('annual_frequency_limit', 'per_visit_limit', 'requires_preauthorization')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50


# ============= PRE-AUTHORIZATION ADMIN =============

@admin.register(PreAuthorization)
class PreAuthorizationAdmin(admin.ModelAdmin):
    list_display = (
        'authorization_number', 'member_link', 'healthcare_provider', 'benefit_service',
        'estimated_cost', 'status', 'planned_procedure_date', 'requested_date'
    )
    list_filter = ('status', 'requested_date', 'planned_procedure_date')
    search_fields = ('authorization_number', 'member__sha_number', 'diagnosis')
    readonly_fields = ('authorization_number', 'requested_date', 'approval_date', 'created_at', 'updated_at')
    date_hierarchy = 'planned_procedure_date'
    
    fieldsets = (
        ('Authorization Details', {
            'fields': ('authorization_number', 'member', 'healthcare_provider', 'benefit_service')
        }),
        ('Request Details', {
            'fields': ('diagnosis', 'procedure_description', 'estimated_cost', 'requested_date', 'planned_procedure_date')
        }),
        ('Supporting Documents', {
            'fields': ('supporting_documents',)
        }),
        ('Approval', {
            'fields': ('status', 'approved_amount', 'approval_date', 'approved_by', 'valid_until')
        }),
        ('Rejection', {
            'fields': ('rejection_reason',)
        }),
        ('Audit', {
            'fields': ('submitted_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    actions = ['approve_preauthorization', 'reject_preauthorization']
    
    def member_link(self, obj):
        url = reverse('admin:sha_system_member_change', args=[obj.member.id])
        return format_html('<a href="{}">{}</a>', url, obj.member.sha_number)
    member_link.short_description = 'Member'
    
    def approve_preauthorization(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='PENDING').update(
            status='APPROVED',
            approval_date=timezone.now(),
            approved_by=request.user
        )
        self.message_user(request, f'{updated} pre-authorization(s) approved.')
    approve_preauthorization.short_description = 'Approve Pre-authorizations'
    
    def reject_preauthorization(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(status='REJECTED')
        self.message_user(request, f'{updated} pre-authorization(s) rejected.')
    reject_preauthorization.short_description = 'Reject Pre-authorizations'
    
    def save_model(self, request, obj, form, change):
        if not obj.authorization_number:
            # Generate authorization number (format: AUTH/YYYY/XXXXXX)
            import datetime
            year = datetime.datetime.now().year
            last_auth = PreAuthorization.objects.filter(
                authorization_number__startswith=f'AUTH/{year}/'
            ).order_by('-authorization_number').first()
            
            if last_auth:
                last_number = int(last_auth.authorization_number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            obj.authorization_number = f'AUTH/{year}/{new_number:06d}'
        
        super().save_model(request, obj, form, change)


# ============= CLAIM ADMIN =============

class ClaimItemInline(admin.TabularInline):
    model = ClaimItem
    extra = 1
    fields = ('benefit_service', 'service_date', 'quantity', 'unit_price', 'total_amount')
    readonly_fields = ('total_amount',)


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = (
        'claim_number', 'member_link', 'healthcare_provider', 'claim_type',
        'claimed_amount', 'approved_amount', 'status', 'submission_date'
    )
    list_filter = ('claim_type', 'status', 'submission_date', 'visit_date')
    search_fields = ('claim_number', 'member__sha_number', 'diagnosis', 'icd_code')
    readonly_fields = (
        'claim_number', 'submission_date', 'review_date', 
        'approval_date', 'payment_date', 'created_at', 'updated_at'
    )
    date_hierarchy = 'submission_date'
    
    fieldsets = (
        ('Claim Details', {
            'fields': ('claim_number', 'member', 'healthcare_provider', 'benefit_package', 'claim_type')
        }),
        ('Visit Details', {
            'fields': ('visit_date', 'admission_date', 'discharge_date')
        }),
        ('Clinical Information', {
            'fields': ('diagnosis', 'icd_code')
        }),
        ('Financial', {
            'fields': ('claimed_amount', 'approved_amount', 'rejected_amount', 'copayment_amount')
        }),
        ('Processing', {
            'fields': ('status', 'submission_date', 'review_date', 'approval_date', 'payment_date')
        }),
        ('Comments', {
            'fields': ('query_comments', 'rejection_reason')
        }),
        ('Pre-authorization', {
            'fields': ('preauthorization',)
        }),
        ('Documents', {
            'fields': ('supporting_documents',)
        }),
        ('Audit', {
            'fields': ('reviewed_by', 'approved_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ClaimItemInline]
    list_per_page = 50
    actions = ['approve_claims', 'reject_claims', 'mark_under_review']
    
    def member_link(self, obj):
        url = reverse('admin:sha_system_member_change', args=[obj.member.id])
        return format_html('<a href="{}">{}</a>', url, obj.member.sha_number)
    member_link.short_description = 'Member'
    
    def approve_claims(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='UNDER_REVIEW').update(
            status='APPROVED',
            approval_date=timezone.now(),
            approved_by=request.user
        )
        self.message_user(request, f'{updated} claim(s) approved.')
    approve_claims.short_description = 'Approve Claims'
    
    def reject_claims(self, request, queryset):
        updated = queryset.exclude(status='PAID').update(status='REJECTED')
        self.message_user(request, f'{updated} claim(s) rejected.')
    reject_claims.short_description = 'Reject Claims'
    
    def mark_under_review(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='SUBMITTED').update(
            status='UNDER_REVIEW',
            review_date=timezone.now()
        )
        self.message_user(request, f'{updated} claim(s) marked as under review.')
    mark_under_review.short_description = 'Mark as Under Review'
    
    def save_model(self, request, obj, form, change):
        if not obj.claim_number:
            # Generate claim number (format: CLM/YYYY/XXXXXX)
            import datetime
            year = datetime.datetime.now().year
            last_claim = Claim.objects.filter(
                claim_number__startswith=f'CLM/{year}/'
            ).order_by('-claim_number').first()
            
            if last_claim:
                last_number = int(last_claim.claim_number.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            obj.claim_number = f'CLM/{year}/{new_number:06d}'
        
        super().save_model(request, obj, form, change)


@admin.register(ClaimItem)
class ClaimItemAdmin(admin.ModelAdmin):
    list_display = (
        'claim', 'benefit_service', 'service_date', 'quantity', 
        'unit_price', 'total_amount', 'approved_amount'
    )
    list_filter = ('service_date', 'benefit_service__service_category')
    search_fields = ('claim__claim_number', 'benefit_service__service_name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Claim Item Details', {
            'fields': ('claim', 'benefit_service', 'service_date')
        }),
        ('Amounts', {
            'fields': ('quantity', 'unit_price', 'total_amount', 'approved_quantity', 'approved_amount')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('System', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50


# ============= PAYMENT ADMIN =============

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'payment_reference', 'healthcare_provider', 'claim_link', 
        'payment_amount', 'payment_date', 'status', 'payment_method'
    )
    list_filter = ('status', 'payment_date', 'payment_method')
    search_fields = ('payment_reference', 'transaction_reference', 'healthcare_provider__facility_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('payment_reference', 'healthcare_provider', 'claim', 'payment_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_date', 'payment_method', 'status')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'account_number', 'transaction_reference')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('processed_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def claim_link(self, obj):
        url = reverse('admin:sha_system_claim_change', args=[obj.claim.id])
        return format_html('<a href="{}">{}</a>', url, obj.claim.claim_number)
    claim_link.short_description = 'Claim'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f'{updated} payment(s) marked as completed.')
    mark_as_completed.short_description = 'Mark as Completed'
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='FAILED')
        self.message_user(request, f'{updated} payment(s) marked as failed.')
    mark_as_failed.short_description = 'Mark as Failed'
    
    def save_model(self, request, obj, form, change):
        if not obj.payment_reference:
            # Generate payment reference (format: PAY/YYYY/XXXXXX)
            import datetime
            year = datetime.datetime.now().year
            last_payment = Payment.objects.filter(
                payment_reference__startswith=f'PAY/{year}/'
            ).order_by('-payment_reference').first()
            
            if last_payment:
                last_number = int(last_payment.payment_reference.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            obj.payment_reference = f'PAY/{year}/{new_number:06d}'
        
        super().save_model(request, obj, form, change)


# ============= ELIGIBILITY CHECK ADMIN =============

@admin.register(EligibilityCheck)
class EligibilityCheckAdmin(admin.ModelAdmin):
    list_display = (
        'member_link', 'healthcare_provider', 'check_date', 
        'is_eligible', 'contributions_up_to_date', 'last_contribution_date'
    )
    list_filter = ('is_eligible', 'contributions_up_to_date', 'check_date')
    search_fields = ('member__sha_number', 'member__first_name', 'member__last_name')
    readonly_fields = ('check_date',)
    date_hierarchy = 'check_date'
    
    fieldsets = (
        ('Check Details', {
            'fields': ('member', 'healthcare_provider', 'check_date')
        }),
        ('Eligibility', {
            'fields': ('is_eligible', 'ineligibility_reason')
        }),
        ('Contribution Status', {
            'fields': ('contributions_up_to_date', 'last_contribution_date')
        }),
        ('Audit', {
            'fields': ('checked_by',),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    
    def member_link(self, obj):
        url = reverse('admin:sha_system_member_change', args=[obj.member.id])
        return format_html('<a href="{}">{}</a>', url, obj.member.sha_number)
    member_link.short_description = 'Member'


# ============= AUDIT LOG ADMIN =============

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_id', 'ip_address')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'model_name', 'object_id', 'ip_address')
    readonly_fields = ('timestamp', 'user', 'action', 'model_name', 'object_id', 'changes', 'ip_address', 'user_agent')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Action Details', {
            'fields': ('timestamp', 'user', 'action', 'model_name', 'object_id')
        }),
        ('Changes', {
            'fields': ('changes',)
        }),
        ('Request Info', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 100
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# ============= NOTIFICATION ADMIN =============

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at', 'read_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'notification_type', 'title', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Related Object', {
            'fields': ('related_object_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 100
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark as Read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark as Unread'


# ============= REPORT ADMIN =============

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_name', 'report_type', 'start_date', 'end_date', 'file_format', 'generated_at', 'generated_by')
    list_filter = ('report_type', 'file_format', 'generated_at')
    search_fields = ('report_name',)
    readonly_fields = ('generated_at',)
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Report Details', {
            'fields': ('report_type', 'report_name', 'start_date', 'end_date')
        }),
        ('Filters', {
            'fields': ('filters',)
        }),
        ('File', {
            'fields': ('file_path', 'file_format')
        }),
        ('Generation Info', {
            'fields': ('generated_by', 'generated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50


# ============= ADMIN SITE CUSTOMIZATION =============

admin.site.site_header = "SHA System Administration"
admin.site.site_title = "SHA Admin Portal"
admin.site.index_title = "Welcome to SHA System Administration"