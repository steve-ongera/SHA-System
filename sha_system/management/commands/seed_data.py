from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from datetime import datetime, timedelta
from decimal import Decimal
import random
from sha_system.models import (
    User, Member, Employer, Contribution, HealthcareProvider,
    BenefitPackage, BenefitService, PreAuthorization, Claim,
    ClaimItem, Payment, EligibilityCheck, AuditLog, Notification, Report
)


class Command(BaseCommand):
    help = 'Seeds the database with realistic Kenyan SHA data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting data seeding...')
        
        # Clear existing data (optional - comment out if you want to preserve data)
        self.stdout.write('Clearing existing data...')
        self.clear_data()
        
        # Seed data in order of dependencies
        self.stdout.write('Creating users...')
        users = self.create_users()
        
        self.stdout.write('Creating employers...')
        employers = self.create_employers(users)
        
        self.stdout.write('Creating healthcare providers...')
        providers = self.create_healthcare_providers(users)
        
        self.stdout.write('Creating members...')
        members = self.create_members(users, employers)
        
        self.stdout.write('Creating benefit packages...')
        packages = self.create_benefit_packages()
        
        self.stdout.write('Creating benefit services...')
        services = self.create_benefit_services(packages)
        
        self.stdout.write('Creating contributions...')
        self.create_contributions(members, employers, users)
        
        self.stdout.write('Creating pre-authorizations...')
        preauths = self.create_preauthorizations(members, providers, services, users)
        
        self.stdout.write('Creating claims...')
        claims = self.create_claims(members, providers, packages, services, preauths, users)
        
        self.stdout.write('Creating payments...')
        self.create_payments(providers, claims, users)
        
        self.stdout.write('Creating eligibility checks...')
        self.create_eligibility_checks(members, providers, users)
        
        self.stdout.write('Creating audit logs...')
        self.create_audit_logs(users)
        
        self.stdout.write('Creating notifications...')
        self.create_notifications(users)
        
        self.stdout.write('Creating reports...')
        self.create_reports(users)
        
        self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))

    def clear_data(self):
        """Clear existing data"""
        Report.objects.all().delete()
        Notification.objects.all().delete()
        AuditLog.objects.all().delete()
        EligibilityCheck.objects.all().delete()
        Payment.objects.all().delete()
        ClaimItem.objects.all().delete()
        Claim.objects.all().delete()
        PreAuthorization.objects.all().delete()
        BenefitService.objects.all().delete()
        BenefitPackage.objects.all().delete()
        Contribution.objects.all().delete()
        Member.objects.all().delete()
        HealthcareProvider.objects.all().delete()
        Employer.objects.all().delete()
        User.objects.all().delete()

    def create_users(self):
        """Create system users with different roles"""
        users = []
        
        # Admin users
        admin = User.objects.create(
            username='admin',
            email='admin@sha.go.ke',
            password=make_password('Admin@2024'),
            role='ADMIN',
            phone_number='0712000001',
            is_verified=True,
            is_staff=True,
            is_superuser=True
        )
        users.append(admin)
        
        # SHA Officers
        for i in range(3):
            user = User.objects.create(
                username=f'sha_officer_{i+1}',
                email=f'officer{i+1}@sha.go.ke',
                password=make_password('SHA@2024'),
                role='SHA_OFFICER',
                phone_number=f'07120000{i+2:02d}',
                is_verified=True
            )
            users.append(user)
        
        # Claims Officers
        for i in range(3):
            user = User.objects.create(
                username=f'claims_officer_{i+1}',
                email=f'claims{i+1}@sha.go.ke',
                password=make_password('Claims@2024'),
                role='CLAIMS_OFFICER',
                phone_number=f'07120000{i+5:02d}',
                is_verified=True
            )
            users.append(user)
        
        # Finance Officers
        for i in range(2):
            user = User.objects.create(
                username=f'finance_officer_{i+1}',
                email=f'finance{i+1}@sha.go.ke',
                password=make_password('Finance@2024'),
                role='FINANCE_OFFICER',
                phone_number=f'07120000{i+8:02d}',
                is_verified=True
            )
            users.append(user)
        
        return users

    def create_employers(self, users):
        """Create employer organizations"""
        employers_data = [
            {
                'company_name': 'Safaricom PLC',
                'kra_pin': 'P051234567A',
                'business_registration_number': 'C.12/2024',
                'email': 'hr@safaricom.co.ke',
                'phone_number': '0722000001',
                'postal_address': 'P.O. Box 66827-00800, Nairobi',
                'physical_address': 'Safaricom House, Waiyaki Way, Westlands',
                'bank_name': 'KCB Bank Kenya',
                'bank_branch': 'Westlands Branch',
                'account_number': '1234567890'
            },
            {
                'company_name': 'Kenya Airways',
                'kra_pin': 'P051234568B',
                'business_registration_number': 'C.13/2024',
                'email': 'hr@kenya-airways.com',
                'phone_number': '0722000002',
                'postal_address': 'P.O. Box 19002-00501, Nairobi',
                'physical_address': 'Airport North Road, Embakasi',
                'bank_name': 'Equity Bank',
                'bank_branch': 'Jomo Kenyatta Branch',
                'account_number': '0234567891'
            },
            {
                'company_name': 'East African Breweries Limited',
                'kra_pin': 'P051234569C',
                'business_registration_number': 'C.14/2024',
                'email': 'hr@eabl.co.ke',
                'phone_number': '0722000003',
                'postal_address': 'P.O. Box 30161-00100, Nairobi',
                'physical_address': 'Ruaraka, Thika Road',
                'bank_name': 'Standard Chartered Bank',
                'bank_branch': 'Industrial Area Branch',
                'account_number': '0134567892'
            },
            {
                'company_name': 'Nairobi County Government',
                'kra_pin': 'P051234570D',
                'business_registration_number': 'G.01/2024',
                'email': 'hr@nairobi.go.ke',
                'phone_number': '0722000004',
                'postal_address': 'P.O. Box 30075-00100, Nairobi',
                'physical_address': 'City Hall, Nairobi CBD',
                'bank_name': 'Co-operative Bank',
                'bank_branch': 'City Hall Branch',
                'account_number': '0144567893'
            },
            {
                'company_name': 'Bamburi Cement Ltd',
                'kra_pin': 'P051234571E',
                'business_registration_number': 'C.15/2024',
                'email': 'hr@bamburi.co.ke',
                'phone_number': '0722000005',
                'postal_address': 'P.O. Box 90186-80100, Mombasa',
                'physical_address': 'Mombasa Road, Athi River',
                'bank_name': 'NCBA Bank',
                'bank_branch': 'Athi River Branch',
                'account_number': '0154567894'
            }
        ]
        
        employers = []
        employer_users = [u for u in users if u.role == 'EMPLOYER'] if any(u.role == 'EMPLOYER' for u in users) else [None] * len(employers_data)
        
        for i, data in enumerate(employers_data):
            employer = Employer.objects.create(
                user=employer_users[i] if i < len(employer_users) else None,
                employer_code=f'EMP{2024000 + i + 1}',
                **data
            )
            employers.append(employer)
        
        return employers

    def create_healthcare_providers(self, users):
        """Create healthcare facilities"""
        providers_data = [
            {
                'facility_name': 'Kenyatta National Hospital',
                'facility_level': 'LEVEL_6',
                'facility_type': 'PUBLIC',
                'license_number': 'KNH/2024/001',
                'kmpdb_number': 'KMPDB/001/2024',
                'email': 'info@knh.or.ke',
                'phone_number': '0732000001',
                'county': 'Nairobi',
                'sub_county': 'Starehe',
                'physical_address': 'Hospital Road, Upper Hill, Nairobi',
                'bank_name': 'KCB Bank Kenya',
                'bank_branch': 'Upper Hill Branch',
                'account_number': '2234567890',
                'contract_start_date': datetime.now().date() - timedelta(days=365),
                'is_contracted': True
            },
            {
                'facility_name': 'Moi Teaching and Referral Hospital',
                'facility_level': 'LEVEL_6',
                'facility_type': 'PUBLIC',
                'license_number': 'MTRH/2024/002',
                'kmpdb_number': 'KMPDB/002/2024',
                'email': 'info@mtrh.go.ke',
                'phone_number': '0732000002',
                'county': 'Uasin Gishu',
                'sub_county': 'Eldoret East',
                'physical_address': 'Nandi Road, Eldoret',
                'bank_name': 'Equity Bank',
                'bank_branch': 'Eldoret Branch',
                'account_number': '2244567891',
                'contract_start_date': datetime.now().date() - timedelta(days=365),
                'is_contracted': True
            },
            {
                'facility_name': 'Nairobi Hospital',
                'facility_level': 'LEVEL_5',
                'facility_type': 'PRIVATE',
                'license_number': 'NH/2024/003',
                'kmpdb_number': 'KMPDB/003/2024',
                'email': 'info@nbihosp.co.ke',
                'phone_number': '0732000003',
                'county': 'Nairobi',
                'sub_county': 'Westlands',
                'physical_address': 'Argwings Kodhek Road, Nairobi',
                'bank_name': 'Standard Chartered Bank',
                'bank_branch': 'Westlands Branch',
                'account_number': '2254567892',
                'contract_start_date': datetime.now().date() - timedelta(days=180),
                'is_contracted': True
            },
            {
                'facility_name': 'Aga Khan University Hospital',
                'facility_level': 'LEVEL_5',
                'facility_type': 'PRIVATE',
                'license_number': 'AKUH/2024/004',
                'kmpdb_number': 'KMPDB/004/2024',
                'email': 'info@aku.edu',
                'phone_number': '0732000004',
                'county': 'Nairobi',
                'sub_county': 'Parklands',
                'physical_address': '3rd Parklands Avenue, Nairobi',
                'bank_name': 'Barclays Bank',
                'bank_branch': 'Parklands Branch',
                'account_number': '2264567893',
                'contract_start_date': datetime.now().date() - timedelta(days=180),
                'is_contracted': True
            },
            {
                'facility_name': 'Coast General Teaching and Referral Hospital',
                'facility_level': 'LEVEL_5',
                'facility_type': 'PUBLIC',
                'license_number': 'CGTRH/2024/005',
                'kmpdb_number': 'KMPDB/005/2024',
                'email': 'info@coastgeneral.go.ke',
                'phone_number': '0732000005',
                'county': 'Mombasa',
                'sub_county': 'Mvita',
                'physical_address': 'Links Road, Mombasa',
                'bank_name': 'Co-operative Bank',
                'bank_branch': 'Mombasa Branch',
                'account_number': '2274567894',
                'contract_start_date': datetime.now().date() - timedelta(days=365),
                'is_contracted': True
            },
            {
                'facility_name': 'Kakamega County General Hospital',
                'facility_level': 'LEVEL_5',
                'facility_type': 'PUBLIC',
                'license_number': 'KCGH/2024/006',
                'kmpdb_number': 'KMPDB/006/2024',
                'email': 'info@kakamegahospital.go.ke',
                'phone_number': '0732000006',
                'county': 'Kakamega',
                'sub_county': 'Lurambi',
                'physical_address': 'Hospital Road, Kakamega',
                'bank_name': 'KCB Bank Kenya',
                'bank_branch': 'Kakamega Branch',
                'account_number': '2284567895',
                'contract_start_date': datetime.now().date() - timedelta(days=365),
                'is_contracted': True
            },
            {
                'facility_name': 'Karen Hospital',
                'facility_level': 'LEVEL_4',
                'facility_type': 'PRIVATE',
                'license_number': 'KH/2024/007',
                'kmpdb_number': 'KMPDB/007/2024',
                'email': 'info@karenhospital.org',
                'phone_number': '0732000007',
                'county': 'Nairobi',
                'sub_county': 'Karen',
                'physical_address': 'Ngong Road, Karen',
                'bank_name': 'Equity Bank',
                'bank_branch': 'Karen Branch',
                'account_number': '2294567896',
                'contract_start_date': datetime.now().date() - timedelta(days=90),
                'is_contracted': True
            },
            {
                'facility_name': 'St. Mary\'s Mission Hospital - Mumias',
                'facility_level': 'LEVEL_4',
                'facility_type': 'FAITH_BASED',
                'license_number': 'SMMH/2024/008',
                'kmpdb_number': 'KMPDB/008/2024',
                'email': 'info@stmarysmumias.org',
                'phone_number': '0732000008',
                'county': 'Kakamega',
                'sub_county': 'Mumias',
                'physical_address': 'Mumias Town',
                'bank_name': 'Co-operative Bank',
                'bank_branch': 'Mumias Branch',
                'account_number': '2304567897',
                'contract_start_date': datetime.now().date() - timedelta(days=365),
                'is_contracted': True
            }
        ]
        
        providers = []
        provider_users = [u for u in users if u.role == 'PROVIDER'] if any(u.role == 'PROVIDER' for u in users) else [None] * len(providers_data)
        
        for i, data in enumerate(providers_data):
            provider = HealthcareProvider.objects.create(
                user=provider_users[i] if i < len(provider_users) else None,
                facility_code=f'HF{2024000 + i + 1}',
                **data
            )
            providers.append(provider)
        
        return providers

    def create_members(self, users, employers):
        """Create members with realistic Kenyan data"""
        kenyan_first_names = [
            'James', 'Mary', 'John', 'Jane', 'Peter', 'Grace', 'David', 'Faith',
            'Joseph', 'Elizabeth', 'Daniel', 'Sarah', 'Samuel', 'Lucy', 'Michael',
            'Ruth', 'Stephen', 'Joyce', 'Paul', 'Agnes', 'Francis', 'Anne',
            'George', 'Margaret', 'William', 'Catherine', 'Robert', 'Rose',
            'Charles', 'Alice', 'Thomas', 'Nancy', 'Richard', 'Susan', 'Anthony'
        ]
        
        kenyan_last_names = [
            'Mwangi', 'Kamau', 'Otieno', 'Ochieng', 'Kimani', 'Njoroge', 'Wanjiru',
            'Achieng', 'Wambui', 'Kariuki', 'Omondi', 'Mutua', 'Kiprotich', 'Cheruiyot',
            'Kiplagat', 'Koech', 'Wambua', 'Muthoni', 'Nyambura', 'Wairimu',
            'Juma', 'Hassan', 'Abdalla', 'Mohamed', 'Waweru', 'Githinji', 'Maina'
        ]
        
        kenyan_counties = [
            'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika',
            'Kakamega', 'Meru', 'Nyeri', 'Kiambu', 'Machakos', 'Uasin Gishu'
        ]
        
        members = []
        member_users = [u for u in users if u.role == 'MEMBER'] if any(u.role == 'MEMBER' for u in users) else []
        
        # Create 50 principal members
        for i in range(50):
            first_name = random.choice(kenyan_first_names)
            last_name = random.choice(kenyan_last_names)
            county = random.choice(kenyan_counties)
            
            member = Member.objects.create(
                user=member_users[i] if i < len(member_users) else None,
                national_id=f'{30000000 + i:08d}',
                first_name=first_name,
                last_name=last_name,
                other_names=random.choice(kenyan_first_names) if random.random() > 0.5 else '',
                date_of_birth=datetime.now().date() - timedelta(days=random.randint(8000, 18000)),
                gender=random.choice(['M', 'F']),
                email=f'{first_name.lower()}.{last_name.lower()}{i}@gmail.com',
                phone_number=f'07{random.randint(10000000, 99999999)}',
                sha_number=f'SHA{2024000000 + i:06d}',
                member_type='PRINCIPAL',
                principal_member=None,
                employment_status=random.choice(['EMPLOYED', 'SELF_EMPLOYED']),
                employer=random.choice(employers) if random.random() > 0.3 else None,
                is_subsidized=random.random() < 0.2,
                county=county,
                sub_county=f'{county} Central',
                ward=f'{county} Ward {random.randint(1, 5)}',
                postal_address=f'P.O. Box {random.randint(1000, 99999)}-{random.randint(10000, 99999)}, {county}'
            )
            members.append(member)
        
        # Create dependents for some principal members
        for principal in random.sample(members, 30):
            num_dependents = random.randint(1, 3)
            for j in range(num_dependents):
                first_name = random.choice(kenyan_first_names)
                dependent = Member.objects.create(
                    national_id=f'{40000000 + len(members):08d}',
                    first_name=first_name,
                    last_name=principal.last_name,
                    date_of_birth=datetime.now().date() - timedelta(days=random.randint(365, 7300)),
                    gender=random.choice(['M', 'F']),
                    email=f'{first_name.lower()}.{principal.last_name.lower()}{len(members)}@gmail.com',
                    phone_number=principal.phone_number,
                    sha_number=f'SHA{2024000000 + len(members):06d}',
                    member_type='DEPENDENT',
                    principal_member=principal,
                    employment_status='UNEMPLOYED',
                    employer=principal.employer,
                    is_subsidized=principal.is_subsidized,
                    county=principal.county,
                    sub_county=principal.sub_county,
                    ward=principal.ward,
                    postal_address=principal.postal_address
                )
                members.append(dependent)
        
        return members

    def create_benefit_packages(self):
        """Create SHA benefit packages"""
        packages = []
        
        # SHIF Package
        shif = BenefitPackage.objects.create(
            package_code='SHIF2024',
            package_name='Social Health Insurance Fund',
            package_type='SHIF',
            description='Core health insurance covering outpatient, inpatient, maternity, and essential services',
            annual_limit=Decimal('1000000.00'),
            applicable_facility_levels=['LEVEL_2', 'LEVEL_3', 'LEVEL_4', 'LEVEL_5', 'LEVEL_6'],
            effective_date=datetime(2024, 1, 1).date()
        )
        packages.append(shif)
        
        # PHCF Package
        phcf = BenefitPackage.objects.create(
            package_code='PHCF2024',
            package_name='Primary Healthcare Fund',
            package_type='PHCF',
            description='Primary and preventive healthcare services at community and dispensary level',
            annual_limit=Decimal('50000.00'),
            applicable_facility_levels=['LEVEL_1', 'LEVEL_2', 'LEVEL_3'],
            effective_date=datetime(2024, 1, 1).date()
        )
        packages.append(phcf)
        
        # ECCIF Package
        eccif = BenefitPackage.objects.create(
            package_code='ECCIF2024',
            package_name='Emergency, Chronic & Critical Illness Fund',
            package_type='ECCIF',
            description='Specialized care for emergencies, chronic diseases, and critical illnesses including cancer, dialysis, and cardiac care',
            annual_limit=Decimal('5000000.00'),
            applicable_facility_levels=['LEVEL_4', 'LEVEL_5', 'LEVEL_6'],
            effective_date=datetime(2024, 1, 1).date()
        )
        packages.append(eccif)
        
        return packages

    def create_benefit_services(self, packages):
        """Create covered services under each package"""
        services = []
        
        shif = packages[0]
        phcf = packages[1]
        eccif = packages[2]
        
        # SHIF Services
        shif_services = [
            {'code': 'OP001', 'name': 'General Outpatient Consultation', 'category': 'OUTPATIENT', 'tariff': '500.00', 'copay': '100.00'},
            {'code': 'OP002', 'name': 'Specialist Consultation', 'category': 'OUTPATIENT', 'tariff': '1500.00', 'copay': '200.00'},
            {'code': 'IP001', 'name': 'General Ward Admission (per day)', 'category': 'INPATIENT', 'tariff': '3000.00', 'copay': '0.00'},
            {'code': 'IP002', 'name': 'High Dependency Unit (per day)', 'category': 'INPATIENT', 'tariff': '10000.00', 'copay': '0.00'},
            {'code': 'MAT001', 'name': 'Normal Delivery', 'category': 'MATERNITY', 'tariff': '15000.00', 'copay': '0.00'},
            {'code': 'MAT002', 'name': 'Caesarean Section', 'category': 'MATERNITY', 'tariff': '35000.00', 'copay': '0.00'},
            {'code': 'SUR001', 'name': 'Minor Surgery', 'category': 'SURGERY', 'tariff': '20000.00', 'copay': '1000.00', 'preauth': True},
            {'code': 'SUR002', 'name': 'Major Surgery', 'category': 'SURGERY', 'tariff': '80000.00', 'copay': '5000.00', 'preauth': True},
            {'code': 'LAB001', 'name': 'Full Blood Count', 'category': 'LABORATORY', 'tariff': '500.00', 'copay': '0.00'},
            {'code': 'LAB002', 'name': 'Comprehensive Metabolic Panel', 'category': 'LABORATORY', 'tariff': '2000.00', 'copay': '100.00'},
            {'code': 'RAD001', 'name': 'X-Ray (Single View)', 'category': 'RADIOLOGY', 'tariff': '1500.00', 'copay': '200.00'},
            {'code': 'RAD002', 'name': 'CT Scan', 'category': 'RADIOLOGY', 'tariff': '12000.00', 'copay': '1000.00', 'preauth': True},
        ]
        
        for service_data in shif_services:
            service = BenefitService.objects.create(
                benefit_package=shif,
                service_code=service_data['code'],
                service_name=service_data['name'],
                service_category=service_data['category'],
                standard_tariff=Decimal(service_data['tariff']),
                copayment_amount=Decimal(service_data['copay']),
                requires_preauthorization=service_data.get('preauth', False)
            )
            services.append(service)
        
        # PHCF Services
        phcf_services = [
            {'code': 'PHC001', 'name': 'Primary Care Consultation', 'category': 'OUTPATIENT', 'tariff': '300.00', 'copay': '50.00'},
            {'code': 'PHC002', 'name': 'Child Immunization', 'category': 'OUTPATIENT', 'tariff': '500.00', 'copay': '0.00'},
            {'code': 'PHC003', 'name': 'Antenatal Care Visit', 'category': 'MATERNITY', 'tariff': '800.00', 'copay': '0.00'},
            {'code': 'PHC004', 'name': 'Basic Laboratory Tests', 'category': 'LABORATORY', 'tariff': '400.00', 'copay': '0.00'},
        ]
        
        for service_data in phcf_services:
            service = BenefitService.objects.create(
                benefit_package=phcf,
                service_code=service_data['code'],
                service_name=service_data['name'],
                service_category=service_data['category'],
                standard_tariff=Decimal(service_data['tariff']),
                copayment_amount=Decimal(service_data['copay'])
            )
            services.append(service)
        
        # ECCIF Services
        eccif_services = [
            {'code': 'DIAL001', 'name': 'Hemodialysis Session', 'category': 'DIALYSIS', 'tariff': '8000.00', 'copay': '500.00'},
            {'code': 'CAN001', 'name': 'Chemotherapy Cycle', 'category': 'CANCER_TREATMENT', 'tariff': '120000.00', 'copay': '10000.00', 'preauth': True},
            {'code': 'CAN002', 'name': 'Radiation Therapy Session', 'category': 'CANCER_TREATMENT', 'tariff': '25000.00', 'copay': '2000.00', 'preauth': True},
            {'code': 'CARD001', 'name': 'Cardiac Catheterization', 'category': 'CARDIOLOGY', 'tariff': '150000.00', 'copay': '15000.00', 'preauth': True},
            {'code': 'CARD002', 'name': 'Open Heart Surgery', 'category': 'CARDIOLOGY', 'tariff': '500000.00', 'copay': '50000.00', 'preauth': True},
            {'code': 'EME001', 'name': 'Emergency Room Treatment', 'category': 'EMERGENCY', 'tariff': '5000.00', 'copay': '0.00'},
            {'code': 'CHR001', 'name': 'Diabetes Management (Monthly)', 'category': 'CHRONIC_ILLNESS', 'tariff': '3000.00', 'copay': '300.00'},
            {'code': 'CHR002', 'name': 'Hypertension Management (Monthly)', 'category': 'CHRONIC_ILLNESS', 'tariff': '2500.00', 'copay': '250.00'},
        ]
        
        for service_data in eccif_services:
            service = BenefitService.objects.create(
                benefit_package=eccif,
                service_code=service_data['code'],
                service_name=service_data['name'],
                service_category=service_data['category'],
                standard_tariff=Decimal(service_data['tariff']),
                copayment_amount=Decimal(service_data['copay']),
                requires_preauthorization=service_data.get('preauth', False)
            )
            services.append(service)
        
        return services

    def create_contributions(self, members, employers, users):
        """Create contribution records"""
        contributions = []
        
        # Get employed members
        employed_members = [m for m in members if m.employment_status == 'EMPLOYED' and m.member_type == 'PRINCIPAL']
        
        for member in employed_members[:40]:  # Create contributions for 40 members
            # Create contributions for last 6 months
            for month_offset in range(6):
                contribution_date = datetime.now().date() - timedelta(days=30 * month_offset)
                contribution_month = contribution_date.replace(day=1)
                
                gross_salary = Decimal(random.randint(25000, 200000))
                contribution_amount = max(Decimal('300.00'), gross_salary * Decimal('0.0275'))
                
                status = 'COMPLETED' if month_offset > 0 else random.choice(['PENDING', 'COMPLETED'])
                
                contribution = Contribution.objects.create(
                    member=member,
                    employer=member.employer,
                    contribution_month=contribution_month,
                    gross_salary=gross_salary,
                    contribution_amount=contribution_amount,
                    payment_method=random.choice(['SALARY_DEDUCTION', 'MPESA', 'BANK_TRANSFER']),
                    transaction_reference=f'TXN{random.randint(100000000, 999999999)}',
                    status=status,
                    submitted_by=random.choice(users)
                )
                contributions.append(contribution)
        
        return contributions

    def create_preauthorizations(self, members, providers, services, users):
        """Create pre-authorization requests"""
        preauths = []
        claims_officers = [u for u in users if u.role == 'CLAIMS_OFFICER']
        
        # Services requiring pre-auth
        preauth_services = [s for s in services if s.requires_preauthorization]
        
        for i in range(20):
            member = random.choice(members)
            provider = random.choice(providers)
            service = random.choice(preauth_services)
            
            planned_date = datetime.now().date() + timedelta(days=random.randint(5, 30))
            status = random.choice(['PENDING', 'APPROVED', 'APPROVED', 'REJECTED'])
            
            preauth = PreAuthorization.objects.create(
                authorization_number=f'PREAUTH{2024000 + i:06d}',
                member=member,
                healthcare_provider=provider,
                benefit_service=service,
                diagnosis=random.choice([
                    'Acute appendicitis requiring surgical intervention',
                    'Chronic kidney disease requiring dialysis',
                    'Malignant breast neoplasm requiring chemotherapy',
                    'Coronary artery disease requiring catheterization',
                    'Severe head trauma requiring CT scan'
                ]),
                procedure_description=service.service_name,
                estimated_cost=service.standard_tariff,
                requested_date=datetime.now().date() - timedelta(days=random.randint(1, 10)),
                planned_procedure_date=planned_date,
                status=status,
                approved_amount=service.standard_tariff if status == 'APPROVED' else None,
                approval_date=timezone.now() if status == 'APPROVED' else None,
                approved_by=random.choice(claims_officers) if status == 'APPROVED' else None,
                rejection_reason='Insufficient documentation provided' if status == 'REJECTED' else '',
                valid_until=planned_date + timedelta(days=30) if status == 'APPROVED' else None,
                submitted_by=random.choice(users)
            )
            preauths.append(preauth)
        
        return preauths

    def create_claims(self, members, providers, packages, services, preauths, users):
        """Create claims"""
        claims = []
        claims_officers = [u for u in users if u.role == 'CLAIMS_OFFICER']
        finance_officers = [u for u in users if u.role == 'FINANCE_OFFICER']
        
        for i in range(60):
            member = random.choice(members)
            provider = random.choice(providers)
            package = random.choice(packages)
            claim_type = random.choice(['OUTPATIENT', 'INPATIENT', 'EMERGENCY'])
            
            visit_date = datetime.now().date() - timedelta(days=random.randint(1, 90))
            
            # Select appropriate services based on package
            package_services = [s for s in services if s.benefit_package == package]
            num_services = random.randint(1, 4)
            claim_services = random.sample(package_services, min(num_services, len(package_services)))
            
            claimed_amount = sum(s.standard_tariff for s in claim_services)
            copayment = sum(s.copayment_amount for s in claim_services)
            
            status_choices = ['SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'PAID', 'REJECTED']
            status_weights = [0.1, 0.15, 0.3, 0.35, 0.1]
            status = random.choices(status_choices, weights=status_weights)[0]
            
            approved_amount = claimed_amount * Decimal(random.uniform(0.85, 1.0)) if status in ['APPROVED', 'PAID'] else None
            
            # Get approved preauth if exists
            preauth = None
            if any(s.requires_preauthorization for s in claim_services):
                approved_preauths = [p for p in preauths if p.status == 'APPROVED' and p.member == member]
                if approved_preauths:
                    preauth = random.choice(approved_preauths)
            
            claim = Claim.objects.create(
                claim_number=f'CLM{2024000000 + i:08d}',
                member=member,
                healthcare_provider=provider,
                benefit_package=package,
                claim_type=claim_type,
                visit_date=visit_date,
                admission_date=visit_date if claim_type == 'INPATIENT' else None,
                discharge_date=visit_date + timedelta(days=random.randint(1, 7)) if claim_type == 'INPATIENT' else None,
                diagnosis=random.choice([
                    'Malaria',
                    'Upper respiratory tract infection',
                    'Hypertension',
                    'Type 2 Diabetes Mellitus',
                    'Acute gastroenteritis',
                    'Pneumonia',
                    'Urinary tract infection',
                    'Road traffic accident injuries'
                ]),
                icd_code=random.choice(['A00', 'J06', 'I10', 'E11', 'A09', 'J18', 'N39', 'V89']),
                claimed_amount=claimed_amount,
                approved_amount=approved_amount,
                copayment_amount=copayment,
                status=status,
                submission_date=timezone.now() - timedelta(days=random.randint(0, 60)),
                review_date=timezone.now() - timedelta(days=random.randint(0, 30)) if status != 'SUBMITTED' else None,
                approval_date=timezone.now() - timedelta(days=random.randint(0, 15)) if status in ['APPROVED', 'PAID'] else None,
                payment_date=timezone.now() - timedelta(days=random.randint(0, 7)) if status == 'PAID' else None,
                rejection_reason='Service not covered under selected package' if status == 'REJECTED' else '',
                preauthorization=preauth,
                reviewed_by=random.choice(claims_officers) if status != 'SUBMITTED' else None,
                approved_by=random.choice(claims_officers) if status in ['APPROVED', 'PAID'] else None
            )
            claims.append(claim)
            
            # Create claim items
            for service in claim_services:
                quantity = random.randint(1, 3)
                total = service.standard_tariff * quantity
                
                ClaimItem.objects.create(
                    claim=claim,
                    benefit_service=service,
                    service_date=visit_date,
                    quantity=quantity,
                    unit_price=service.standard_tariff,
                    total_amount=total,
                    approved_quantity=quantity if status in ['APPROVED', 'PAID'] else None,
                    approved_amount=total * Decimal(random.uniform(0.9, 1.0)) if status in ['APPROVED', 'PAID'] else None
                )
        
        return claims

    def create_payments(self, providers, claims, users):
        """Create payment records"""
        payments = []
        finance_officers = [u for u in users if u.role == 'FINANCE_OFFICER']
        
        # Get paid claims
        paid_claims = [c for c in claims if c.status == 'PAID' and c.approved_amount]
        
        for claim in paid_claims[:40]:
            payment = Payment.objects.create(
                payment_reference=f'PAY{random.randint(100000000, 999999999)}',
                healthcare_provider=claim.healthcare_provider,
                claim=claim,
                payment_amount=claim.approved_amount,
                payment_date=claim.payment_date.date() if claim.payment_date else datetime.now().date(),
                payment_method='Bank Transfer',
                status=random.choice(['COMPLETED', 'COMPLETED', 'PROCESSING']),
                bank_name=claim.healthcare_provider.bank_name,
                account_number=claim.healthcare_provider.account_number,
                transaction_reference=f'BANK{random.randint(1000000, 9999999)}',
                processed_by=random.choice(finance_officers),
                notes='Payment processed successfully'
            )
            payments.append(payment)
        
        return payments

    def create_eligibility_checks(self, members, providers, users):
        """Create eligibility check records"""
        checks = []
        
        for i in range(100):
            member = random.choice(members)
            provider = random.choice(providers)
            
            # Check if member has recent contributions
            has_contributions = random.random() > 0.15
            
            check = EligibilityCheck.objects.create(
                member=member,
                healthcare_provider=provider,
                is_eligible=has_contributions and member.is_active,
                ineligibility_reason='' if has_contributions else 'No recent contributions found',
                contributions_up_to_date=has_contributions,
                last_contribution_date=datetime.now().date() - timedelta(days=random.randint(1, 60)) if has_contributions else None,
                checked_by=random.choice(users)
            )
            checks.append(check)
        
        return checks

    def create_audit_logs(self, users):
        """Create audit log entries"""
        logs = []
        
        actions = ['CREATE', 'UPDATE', 'APPROVE', 'REJECT', 'PAYMENT', 'LOGIN']
        models = ['Claim', 'Member', 'Contribution', 'PreAuthorization', 'Payment']
        
        for i in range(200):
            log = AuditLog.objects.create(
                user=random.choice(users),
                action=random.choice(actions),
                model_name=random.choice(models),
                object_id=str(i + 1000),
                changes={'field': 'status', 'old': 'SUBMITTED', 'new': 'APPROVED'},
                ip_address=f'192.168.1.{random.randint(1, 254)}',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            logs.append(log)
        
        return logs

    def create_notifications(self, users):
        """Create user notifications"""
        notifications = []
        
        notification_types = [
            'CONTRIBUTION_RECEIVED',
            'CLAIM_SUBMITTED',
            'CLAIM_APPROVED',
            'PAYMENT_MADE',
            'PREAUTH_APPROVED'
        ]
        
        for user in users:
            for i in range(random.randint(3, 10)):
                notif_type = random.choice(notification_types)
                
                titles = {
                    'CONTRIBUTION_RECEIVED': 'Contribution Received',
                    'CLAIM_SUBMITTED': 'New Claim Submitted',
                    'CLAIM_APPROVED': 'Claim Approved',
                    'PAYMENT_MADE': 'Payment Processed',
                    'PREAUTH_APPROVED': 'Pre-authorization Approved'
                }
                
                messages = {
                    'CONTRIBUTION_RECEIVED': 'Your SHA contribution of KES 2,750.00 has been received.',
                    'CLAIM_SUBMITTED': 'A new claim has been submitted for review.',
                    'CLAIM_APPROVED': 'Your claim CLM20240001 has been approved for KES 15,000.',
                    'PAYMENT_MADE': 'Payment of KES 50,000 has been processed to your account.',
                    'PREAUTH_APPROVED': 'Pre-authorization PREAUTH2024001 has been approved.'
                }
                
                notification = Notification.objects.create(
                    user=user,
                    notification_type=notif_type,
                    title=titles[notif_type],
                    message=messages[notif_type],
                    is_read=random.random() > 0.4,
                    read_at=timezone.now() - timedelta(hours=random.randint(1, 72)) if random.random() > 0.4 else None,
                    related_object_type='Claim',
                    related_object_id=str(random.randint(1000, 9999))
                )
                notifications.append(notification)
        
        return notifications

    def create_reports(self, users):
        """Create report records"""
        reports = []
        
        report_types = [
            'CONTRIBUTION_SUMMARY',
            'CLAIMS_REPORT',
            'PAYMENT_REPORT',
            'UTILIZATION_REPORT',
            'PROVIDER_PERFORMANCE'
        ]
        
        for i in range(15):
            report_type = random.choice(report_types)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            report = Report.objects.create(
                report_type=report_type,
                report_name=f'{report_type.replace("_", " ").title()} - {start_date.strftime("%B %Y")}',
                start_date=start_date,
                end_date=end_date,
                filters={'county': 'Nairobi', 'status': 'APPROVED'},
                file_path=f'/reports/{report_type.lower()}_{start_date.strftime("%Y%m")}.pdf',
                file_format='PDF',
                generated_by=random.choice([u for u in users if u.role in ['SHA_OFFICER', 'FINANCE_OFFICER']])
            )
            reports.append(report)
        
        return reports