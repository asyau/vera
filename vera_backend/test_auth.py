#!/usr/bin/env python3
"""
Test script for authentication system
"""
import json

import requests

BASE_URL = "http://localhost:8000/api"


def test_signup():
    """Test user signup"""
    print("Testing user signup...")

    signup_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "role": "employee",
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        print(f"Signup Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Signup successful!")
            print(f"Token: {data['token'][:50]}...")
            print(f"User: {data['user']['name']} ({data['user']['role']})")
            return data["token"]
        else:
            print(f"❌ Signup failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return None


def test_login():
    """Test user login"""
    print("\nTesting user login...")

    login_data = {"email": "test@example.com", "password": "password123"}

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"Token: {data['token'][:50]}...")
            print(f"User: {data['user']['name']} ({data['user']['role']})")
            return data["token"]
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None


def test_get_current_user(token):
    """Test getting current user info"""
    print("\nTesting get current user...")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"Get User Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Get current user successful!")
            print(f"User: {data['name']} ({data['role']})")
            return True
        else:
            print(f"❌ Get current user failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Get current user error: {e}")
        return False


def test_supervisor_signup():
    """Test supervisor signup"""
    print("\nTesting supervisor signup...")

    signup_data = {
        "name": "Supervisor User",
        "email": "supervisor@example.com",
        "password": "password123",
        "role": "supervisor",
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        print(f"Supervisor Signup Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Supervisor signup successful!")
            print(f"User: {data['user']['name']} ({data['user']['role']})")
            return data["token"]
        else:
            print(f"❌ Supervisor signup failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Supervisor signup error: {e}")
        return None


def main():
    print("🧪 Testing Authentication System")
    print("=" * 50)

    # Test employee signup and login
    token = test_signup()
    if token:
        test_get_current_user(token)

    # Test login with existing user
    login_token = test_login()
    if login_token:
        test_get_current_user(login_token)

    # Test supervisor signup
    supervisor_token = test_supervisor_signup()
    if supervisor_token:
        test_get_current_user(supervisor_token)

    print("\n" + "=" * 50)
    print("🏁 Authentication tests completed!")


if __name__ == "__main__":
    main()
