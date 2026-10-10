#!/usr/bin/env python3
"""
Test script to demonstrate patient self-registration workflow
"""

import requests
import json
from datetime import date

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_patient_signup():
    """Test the patient self-registration workflow"""
    
    print("=== TESTING PATIENT SIGNUP WORKFLOW ===\n")
    
    # Test data for patient signup
    patient_signup_data = {
        # User data
        "username": "jane_patient",
        "email": "jane.patient@example.com", 
        "password": "patient123",
        
        # Patient data
        "fullname": "Jane Patient",
        "dob": "1990-05-15",
        "age": 33,
        "gender": "Female",
        "symptoms": "Chest pain, shortness of breath",
        "conditions": "None",
        "phone": "+1234567890",
        "address": "123 Main St, City, State",
        "emergency_contact_name": "John Patient",
        "emergency_contact_phone": "+0987654321"
    }
    
    print("1. Patient Self-Registration")
    print(f"   Data: {json.dumps(patient_signup_data, indent=2)}\n")
    
    # Patient signup
    response = requests.post(
        f"{BASE_URL}/auth/patient-signup",
        json=patient_signup_data
    )
    
    if response.status_code == 200:
        patient = response.json()
        print(f"   ✅ SUCCESS: Patient created!")
        print(f"   Patient ID: {patient['patient_id']}")
        print(f"   User ID: {patient['user_id']}")
        print(f"   Full Name: {patient['fullname']}\n")
        
        user_id = patient['user_id']
        
        # Test login with new patient credentials
        print("2. Patient Login Test")
        login_data = {
            "username": patient_signup_data['username'],
            "password": patient_signup_data['password']
        }
        
        login_response = requests.post(
            f"{BASE_URL}/auth/login/json",
            json=login_data
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data['access_token']
            print(f"   ✅ SUCCESS: Patient login successful!")
            print(f"   Token: {access_token[:20]}...\n")
            
            # Test accessing patient's own records
            print("3. Patient Access to Own Records")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Get patient's own data
            patients_response = requests.get(
                f"{BASE_URL}/patients/",
                headers=headers
            )
            
            if patients_response.status_code == 200:
                patients = patients_response.json()
                print(f"   ✅ SUCCESS: Patient can access their records!")
                print(f"   Found {len(patients)} patient record(s)")
                for p in patients:
                    print(f"   - Patient: {p['fullname']} (ID: {p['patient_id']})")
                print()
            else:
                print(f"   ❌ FAILED: Cannot access patient records - {patients_response.status_code}")
                print(f"   Error: {patients_response.text}\n")
            
            # Test getting current user info
            print("4. Get Current User Info")
            me_response = requests.get(
                f"{BASE_URL}/auth/me",
                headers=headers
            )
            
            if me_response.status_code == 200:
                user_info = me_response.json()
                print(f"   ✅ SUCCESS: Got user info!")
                print(f"   Username: {user_info['username']}")
                print(f"   Email: {user_info['email']}")
                print(f"   Active: {user_info['is_active']}")
                print(f"   Complete: {user_info['is_complete']}\n")
            else:
                print(f"   ❌ FAILED: Cannot get user info - {me_response.status_code}\n")
                
        else:
            print(f"   ❌ FAILED: Patient login failed - {login_response.status_code}")
            print(f"   Error: {login_response.text}\n")
            
    else:
        print(f"   ❌ FAILED: Patient signup failed - {response.status_code}")
        print(f"   Error: {response.text}\n")
    
    # Test duplicate registration (should fail)
    print("5. Test Duplicate Registration (Should Fail)")
    duplicate_response = requests.post(
        f"{BASE_URL}/auth/patient-signup",
        json=patient_signup_data
    )
    
    if duplicate_response.status_code == 400:
        print(f"   ✅ SUCCESS: Duplicate registration properly rejected!")
        print(f"   Error message: {duplicate_response.json()['detail']}\n")
    else:
        print(f"   ❌ UNEXPECTED: Duplicate registration not rejected - {duplicate_response.status_code}\n")
    
    print("=== PATIENT SIGNUP WORKFLOW TEST COMPLETE ===")

if __name__ == "__main__":
    try:
        test_patient_signup()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to API server!")
        print("Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc() 