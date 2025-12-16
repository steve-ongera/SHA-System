# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import (
    Member, Employer, Contribution, HealthcareProvider,
    Claim, Payment, PreAuthorization, EligibilityCheck
)


@login_required
def admin_dashboard(request):
    """
    Main admin dashboard view with comprehensive statistics
    """
    # Date ranges
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    
    # ========== MEMBER STATISTICS ==========
    total_members = Member.objects.filter(is_active=True).count()
    principal_members = Member.objects.filter(member_type='PRINCIPAL', is_active=True).count()
    dependent_members = Member.objects.filter(member_type='DEPENDENT', is_active=True).count()
    new_members_this_month = Member.objects.filter(
        registration_date__gte=this_month_start
    ).count()
    new_members_last_month = Member.objects.filter(
        registration_date__gte=last_month_start,
        registration_date__lt=this_month_start
    ).count()
    
    # Calculate member growth percentage
    if new_members_last_month > 0:
        member_growth = ((new_members_this_month - new_members_last_month) / new_members_last_month) * 100
    else:
        member_growth = 100 if new_members_this_month > 0 else 0
    
    # ========== CONTRIBUTION STATISTICS ==========
    total_contributions = Contribution.objects.filter(status='COMPLETED').aggregate(
        total=Sum('contribution_amount')
    )['total'] or Decimal('0.00')
    
    contributions_this_month = Contribution.objects.filter(
        contribution_month__gte=this_month_start,
        status='COMPLETED'
    ).aggregate(total=Sum('contribution_amount'))['total'] or Decimal('0.00')
    
    contributions_last_month = Contribution.objects.filter(
        contribution_month__gte=last_month_start,
        contribution_month__lt=this_month_start,
        status='COMPLETED'
    ).aggregate(total=Sum('contribution_amount'))['total'] or Decimal('0.00')
    
    pending_contributions = Contribution.objects.filter(status='PENDING').count()
    
    # Calculate contribution growth
    if contributions_last_month > 0:
        contribution_growth = ((contributions_this_month - contributions_last_month) / contributions_last_month) * 100
    else:
        contribution_growth = 100 if contributions_this_month > 0 else 0
    
    # ========== CLAIM STATISTICS ==========
    total_claims = Claim.objects.count()
    pending_claims = Claim.objects.filter(
        status__in=['SUBMITTED', 'UNDER_REVIEW']
    ).count()
    approved_claims = Claim.objects.filter(status='APPROVED').count()
    paid_claims = Claim.objects.filter(status='PAID').count()
    rejected_claims = Claim.objects.filter(status='REJECTED').count()
    
    total_claimed_amount = Claim.objects.filter(
        status__in=['APPROVED', 'PAID']
    ).aggregate(total=Sum('approved_amount'))['total'] or Decimal('0.00')
    
    claims_this_month = Claim.objects.filter(
        submission_date__gte=this_month_start
    ).count()
    
    claims_last_month = Claim.objects.filter(
        submission_date__gte=last_month_start,
        submission_date__lt=this_month_start
    ).count()
    
    # Calculate claims growth
    if claims_last_month > 0:
        claims_growth = ((claims_this_month - claims_last_month) / claims_last_month) * 100
    else:
        claims_growth = 100 if claims_this_month > 0 else 0
    
    # ========== PAYMENT STATISTICS ==========
    total_payments = Payment.objects.filter(status='COMPLETED').aggregate(
        total=Sum('payment_amount')
    )['total'] or Decimal('0.00')
    
    pending_payments = Payment.objects.filter(status__in=['PENDING', 'PROCESSING']).count()
    pending_payment_amount = Payment.objects.filter(
        status__in=['PENDING', 'PROCESSING']
    ).aggregate(total=Sum('payment_amount'))['total'] or Decimal('0.00')
    
    payments_this_month = Payment.objects.filter(
        payment_date__gte=this_month_start,
        status='COMPLETED'
    ).aggregate(total=Sum('payment_amount'))['total'] or Decimal('0.00')
    
    # ========== HEALTHCARE PROVIDER STATISTICS ==========
    total_providers = HealthcareProvider.objects.filter(is_active=True).count()
    contracted_providers = HealthcareProvider.objects.filter(
        is_active=True,
        is_contracted=True
    ).count()
    
    # ========== EMPLOYER STATISTICS ==========
    total_employers = Employer.objects.filter(is_active=True).count()
    
    # ========== PRE-AUTHORIZATION STATISTICS ==========
    pending_preauth = PreAuthorization.objects.filter(status='PENDING').count()
    
    # ========== RECENT ACTIVITIES ==========
    recent_claims = Claim.objects.select_related(
        'member', 'healthcare_provider'
    ).order_by('-submission_date')[:10]
    
    recent_payments = Payment.objects.select_related(
        'healthcare_provider', 'claim'
    ).order_by('-created_at')[:10]
    
    recent_members = Member.objects.order_by('-registration_date')[:10]
    
    # ========== CLAIM STATUS DISTRIBUTION ==========
    claim_status_data = {
        'labels': ['Submitted', 'Under Review', 'Approved', 'Paid', 'Rejected'],
        'data': [
            Claim.objects.filter(status='SUBMITTED').count(),
            Claim.objects.filter(status='UNDER_REVIEW').count(),
            approved_claims,
            paid_claims,
            rejected_claims,
        ]
    }
    
    # ========== MONTHLY CONTRIBUTIONS TREND (Last 6 months) ==========
    monthly_contributions = []
    monthly_labels = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if i > 0:
            next_month = (month_start + timedelta(days=32)).replace(day=1)
        else:
            next_month = today + timedelta(days=1)
        
        amount = Contribution.objects.filter(
            contribution_month__gte=month_start,
            contribution_month__lt=next_month,
            status='COMPLETED'
        ).aggregate(total=Sum('contribution_amount'))['total'] or 0
        
        monthly_contributions.append(float(amount))
        monthly_labels.append(month_start.strftime('%b %Y'))
    
    contributions_trend = {
        'labels': monthly_labels,
        'data': monthly_contributions
    }
    
    # ========== TOP HEALTHCARE PROVIDERS BY CLAIMS ==========
    top_providers = HealthcareProvider.objects.annotate(
        claim_count=Count('claims')
    ).order_by('-claim_count')[:5]
    
    provider_stats = {
        'labels': [p.facility_name[:20] for p in top_providers],
        'data': [p.claim_count for p in top_providers]
    }
    
    # ========== MEMBER DISTRIBUTION BY COUNTY ==========
    top_counties = Member.objects.values('county').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    county_distribution = {
        'labels': [c['county'] for c in top_counties],
        'data': [c['count'] for c in top_counties]
    }
    
    context = {
        # Member Stats
        'total_members': total_members,
        'principal_members': principal_members,
        'dependent_members': dependent_members,
        'new_members_this_month': new_members_this_month,
        'member_growth': round(member_growth, 1),
        
        # Contribution Stats
        'total_contributions': total_contributions,
        'contributions_this_month': contributions_this_month,
        'pending_contributions': pending_contributions,
        'contribution_growth': round(contribution_growth, 1),
        
        # Claim Stats
        'total_claims': total_claims,
        'pending_claims': pending_claims,
        'approved_claims': approved_claims,
        'paid_claims': paid_claims,
        'rejected_claims': rejected_claims,
        'total_claimed_amount': total_claimed_amount,
        'claims_growth': round(claims_growth, 1),
        
        # Payment Stats
        'total_payments': total_payments,
        'pending_payments': pending_payments,
        'pending_payment_amount': pending_payment_amount,
        'payments_this_month': payments_this_month,
        
        # Provider & Employer Stats
        'total_providers': total_providers,
        'contracted_providers': contracted_providers,
        'total_employers': total_employers,
        
        # Pre-authorization
        'pending_preauth': pending_preauth,
        
        # Recent Activities
        'recent_claims': recent_claims,
        'recent_payments': recent_payments,
        'recent_members': recent_members,
        
        # Chart Data
        'claim_status_data': claim_status_data,
        'contributions_trend': contributions_trend,
        'provider_stats': provider_stats,
        'county_distribution': county_distribution,
    }
    
    return render(request, 'admin/dashboard.html', context)