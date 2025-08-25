import pandas as pd
import random
from faker import Faker
from datetime import datetime

fake = Faker('en_US')

num_rows = 100

hospitals = [
    'Riyadh General Hospital',
    'Jeddah Medical Center',
    'Dammam Health Complex',
    'Makkah Specialty Hospital'
]
doctors = [
    'Dr. Nora Al-Ali',
    'Dr. Saeed Al-Harbi',
    'Dr. Lina Al-Mutairi',
    'Dr. Khaled Al-Qahtani'
]
diagnoses = [
    'Diabetes Type 2',
    'Hypertension',
    'Asthma',
    'Cardiac Arrest',
    'Migraine',
    'Arthritis'
]

disease_names = [
    'Influenza',
    'COVID-19',
    'Tuberculosis',
    'Hepatitis B',
    'Chickenpox',
    'Malaria'
]

cities = [
    'Riyadh', 'Jeddah', 'Dammam', 'Mecca', 'Medina', 'Abha', 'Tabuk', 'Hail'
]

hospital_regions = {
    'Riyadh General Hospital': 'Central Region',
    'Jeddah Medical Center': 'Western Region',
    'Dammam Health Complex': 'Eastern Region',
    'Makkah Specialty Hospital': 'Western Region'
}

genders = ['M', 'F']

def calculate_age_group(dob):
    age = (datetime.today().date() - dob).days // 365
    if age < 20:
        return '0-19'
    elif age < 30:
        return '20-29'
    elif age < 40:
        return '30-39'
    elif age < 50:
        return '40-49'
    elif age < 60:
        return '50-59'
    else:
        return '60+'

def random_report_date():
    year = random.choice([2023, 2024, 2025])
    month = random.choice(range(1, 13))
    return datetime(year, month, 1).date()

data = []
for i in range(num_rows):
    full_name = fake.name()
    national_id = fake.random_number(digits=10, fix_len=True)
    dob = fake.date_of_birth(minimum_age=18, maximum_age=80)
    gender = random.choice(genders)
    diagnosis = random.choice(diagnoses)
    admission_date = fake.date_between(start_date='-3y', end_date='today')
    discharge_date = fake.date_between(start_date=admission_date, end_date='today')
    doctor_name = random.choice(doctors)
    hospital_name = random.choice(hospitals)
    email = fake.email()
    patient_id = str(i+1).zfill(3)
    
    # New columns
    disease_name = random.choice(disease_names)
    city = random.choice(cities)
    hospital_region = hospital_regions[hospital_name]
    
    admission_count = random.randint(5, 200)  # aggregated monthly admission count
    
    recovery_rate = round(random.uniform(85.0, 99.9), 1)  # percent
    
    age_group = calculate_age_group(dob)
    
    report_date = random_report_date()
    
    data.append([
        patient_id,
        full_name,
        national_id,
        dob,
        gender,
        diagnosis,
        admission_date,
        discharge_date,
        doctor_name,
        hospital_name,
        email,
        disease_name,
        city,
        hospital_region,
        admission_count,
        recovery_rate,
        age_group,
        report_date
    ])

columns = [
    'Patient_ID',
    'Full_Name',
    'National_ID',
    'Date_of_Birth',
    'Gender',
    'Diagnosis',
    'Admission_Date',
    'Discharge_Date',
    'Doctor_Name',
    'Hospital_Name',
    'Email',
    'Disease_Name',
    'City',
    'Hospital_Region',
    'Admission_Count',
    'Recovery_Rate',
    'Age_Group',
    'Report_Date'
]

df = pd.DataFrame(data, columns=columns)

# Save to CSV file
df.to_csv("Hospital.csv", index=False)

print("File saved: Hospital.csv")
