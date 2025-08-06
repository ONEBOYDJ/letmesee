#!/usr/bin/env python3
"""
Backend API Testing Suite for Story Publishing Platform
Tests all backend endpoints according to test_result.md requirements
"""

import requests
import json
import os
import sys
from datetime import datetime
import uuid

# Load backend URL from frontend .env file
def load_backend_url():
    env_path = "/app/frontend/.env"
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                return line.split('=', 1)[1].strip()
    return None

BASE_URL = load_backend_url()
if not BASE_URL:
    print("❌ Could not load REACT_APP_BACKEND_URL from frontend/.env")
    sys.exit(1)

API_BASE = f"{BASE_URL}/api"
print(f"🔗 Testing backend at: {API_BASE}")

# Test data
TEST_USER = {
    "username": f"testuser_{uuid.uuid4().hex[:8]}",
    "password": "testpass123",
    "email": "testuser@example.com"
}

ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

TEST_STORY = {
    "title": "My Amazing Adventure",
    "content": "<h1>Chapter 1</h1><p>It was a dark and stormy night when I discovered the secret of the ancient library...</p><p>The books seemed to whisper secrets of forgotten worlds.</p>"
}

# Global variables for tokens and IDs
user_token = None
admin_token = None
story_id = None
test_results = []

def log_test(test_name, success, message="", details=None):
    """Log test results"""
    status = "✅" if success else "❌"
    result = {
        "test": test_name,
        "success": success,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    print(f"{status} {test_name}: {message}")
    if details and not success:
        print(f"   Details: {details}")

def make_request(method, endpoint, data=None, headers=None, expected_status=None):
    """Make HTTP request with error handling"""
    url = f"{API_BASE}{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if expected_status and response.status_code != expected_status:
            return None, f"Expected status {expected_status}, got {response.status_code}: {response.text}"
        
        return response, None
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {str(e)}"

def test_user_registration():
    """Test user registration endpoint"""
    print("\n🧪 Testing User Registration...")
    
    response, error = make_request("POST", "/auth/register", TEST_USER, expected_status=200)
    if error:
        log_test("User Registration", False, "Registration failed", error)
        return False
    
    try:
        data = response.json()
        if "access_token" not in data or "user" not in data:
            log_test("User Registration", False, "Missing token or user in response", data)
            return False
        
        global user_token
        user_token = data["access_token"]
        user_info = data["user"]
        
        if user_info["username"] != TEST_USER["username"]:
            log_test("User Registration", False, "Username mismatch in response")
            return False
        
        if user_info["is_admin"] != False:
            log_test("User Registration", False, "New user should not be admin")
            return False
        
        log_test("User Registration", True, f"User {TEST_USER['username']} registered successfully")
        return True
        
    except json.JSONDecodeError:
        log_test("User Registration", False, "Invalid JSON response", response.text)
        return False

def test_duplicate_registration():
    """Test duplicate user registration should fail"""
    print("\n🧪 Testing Duplicate Registration...")
    
    response, error = make_request("POST", "/auth/register", TEST_USER)
    if not response:
        log_test("Duplicate Registration Check", False, "Request failed", error)
        return False
    
    if response.status_code == 400:
        log_test("Duplicate Registration Check", True, "Correctly rejected duplicate username")
        return True
    else:
        log_test("Duplicate Registration Check", False, f"Expected 400, got {response.status_code}")
        return False

def test_user_login():
    """Test user login endpoint"""
    print("\n🧪 Testing User Login...")
    
    login_data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    
    response, error = make_request("POST", "/auth/login", login_data, expected_status=200)
    if error:
        log_test("User Login", False, "Login failed", error)
        return False
    
    try:
        data = response.json()
        if "access_token" not in data or "user" not in data:
            log_test("User Login", False, "Missing token or user in response")
            return False
        
        # Update token (should be same as registration token)
        global user_token
        user_token = data["access_token"]
        
        log_test("User Login", True, f"User {TEST_USER['username']} logged in successfully")
        return True
        
    except json.JSONDecodeError:
        log_test("User Login", False, "Invalid JSON response", response.text)
        return False

def test_admin_login():
    """Test admin login with default credentials"""
    print("\n🧪 Testing Admin Login...")
    
    response, error = make_request("POST", "/auth/login", ADMIN_CREDENTIALS, expected_status=200)
    if error:
        log_test("Admin Login", False, "Admin login failed", error)
        return False
    
    try:
        data = response.json()
        if "access_token" not in data or "user" not in data:
            log_test("Admin Login", False, "Missing token or user in response")
            return False
        
        global admin_token
        admin_token = data["access_token"]
        user_info = data["user"]
        
        if not user_info.get("is_admin", False):
            log_test("Admin Login", False, "Admin user should have is_admin=True")
            return False
        
        log_test("Admin Login", True, "Admin logged in successfully with admin/admin123")
        return True
        
    except json.JSONDecodeError:
        log_test("Admin Login", False, "Invalid JSON response", response.text)
        return False

def test_jwt_validation():
    """Test JWT token validation with /auth/me endpoint"""
    print("\n🧪 Testing JWT Token Validation...")
    
    if not user_token:
        log_test("JWT Validation", False, "No user token available")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response, error = make_request("GET", "/auth/me", headers=headers, expected_status=200)
    
    if error:
        log_test("JWT Validation", False, "Token validation failed", error)
        return False
    
    try:
        user_info = response.json()
        if user_info["username"] != TEST_USER["username"]:
            log_test("JWT Validation", False, "Token returned wrong user")
            return False
        
        log_test("JWT Validation", True, "JWT token validation successful")
        return True
        
    except json.JSONDecodeError:
        log_test("JWT Validation", False, "Invalid JSON response", response.text)
        return False

def test_story_creation():
    """Test story creation endpoint"""
    print("\n🧪 Testing Story Creation...")
    
    if not user_token:
        log_test("Story Creation", False, "No user token available")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response, error = make_request("POST", "/stories", TEST_STORY, headers=headers, expected_status=200)
    
    if error:
        log_test("Story Creation", False, "Story creation failed", error)
        return False
    
    try:
        story_data = response.json()
        global story_id
        story_id = story_data["id"]
        
        if story_data["title"] != TEST_STORY["title"]:
            log_test("Story Creation", False, "Story title mismatch")
            return False
        
        if story_data["status"] != "pending":
            log_test("Story Creation", False, "New story should have pending status")
            return False
        
        if story_data["author_username"] != TEST_USER["username"]:
            log_test("Story Creation", False, "Story author mismatch")
            return False
        
        log_test("Story Creation", True, f"Story '{TEST_STORY['title']}' created successfully")
        return True
        
    except json.JSONDecodeError:
        log_test("Story Creation", False, "Invalid JSON response", response.text)
        return False

def test_my_stories():
    """Test retrieving user's own stories"""
    print("\n🧪 Testing My Stories Retrieval...")
    
    if not user_token:
        log_test("My Stories", False, "No user token available")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response, error = make_request("GET", "/stories/my", headers=headers, expected_status=200)
    
    if error:
        log_test("My Stories", False, "Failed to retrieve my stories", error)
        return False
    
    try:
        stories = response.json()
        if not isinstance(stories, list):
            log_test("My Stories", False, "Response should be a list")
            return False
        
        if len(stories) == 0:
            log_test("My Stories", False, "Should have at least one story")
            return False
        
        # Check if our created story is in the list
        found_story = False
        for story in stories:
            if story["id"] == story_id:
                found_story = True
                break
        
        if not found_story:
            log_test("My Stories", False, "Created story not found in my stories")
            return False
        
        log_test("My Stories", True, f"Retrieved {len(stories)} stories successfully")
        return True
        
    except json.JSONDecodeError:
        log_test("My Stories", False, "Invalid JSON response", response.text)
        return False

def test_pending_stories_admin():
    """Test admin access to pending stories"""
    print("\n🧪 Testing Admin Pending Stories Access...")
    
    if not admin_token:
        log_test("Admin Pending Stories", False, "No admin token available")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    response, error = make_request("GET", "/stories/pending", headers=headers, expected_status=200)
    
    if error:
        log_test("Admin Pending Stories", False, "Failed to retrieve pending stories", error)
        return False
    
    try:
        stories = response.json()
        if not isinstance(stories, list):
            log_test("Admin Pending Stories", False, "Response should be a list")
            return False
        
        # Should have at least our pending story
        found_pending = False
        for story in stories:
            if story["id"] == story_id and story["status"] == "pending":
                found_pending = True
                break
        
        if not found_pending:
            log_test("Admin Pending Stories", False, "Our pending story not found")
            return False
        
        log_test("Admin Pending Stories", True, f"Retrieved {len(stories)} pending stories")
        return True
        
    except json.JSONDecodeError:
        log_test("Admin Pending Stories", False, "Invalid JSON response", response.text)
        return False

def test_pending_stories_user_forbidden():
    """Test that regular users cannot access pending stories"""
    print("\n🧪 Testing User Access to Pending Stories (Should Fail)...")
    
    if not user_token:
        log_test("User Pending Stories Forbidden", False, "No user token available")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response, error = make_request("GET", "/stories/pending", headers=headers)
    
    if not response:
        log_test("User Pending Stories Forbidden", False, "Request failed", error)
        return False
    
    if response.status_code == 403:
        log_test("User Pending Stories Forbidden", True, "Correctly denied access to regular user")
        return True
    else:
        log_test("User Pending Stories Forbidden", False, f"Expected 403, got {response.status_code}")
        return False

def test_story_approval():
    """Test admin story approval"""
    print("\n🧪 Testing Story Approval by Admin...")
    
    if not admin_token or not story_id:
        log_test("Story Approval", False, "Missing admin token or story ID")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    approval_data = {"status": "approved"}
    
    response, error = make_request("PUT", f"/stories/{story_id}/moderate", approval_data, headers=headers, expected_status=200)
    
    if error:
        log_test("Story Approval", False, "Story approval failed", error)
        return False
    
    try:
        result = response.json()
        if "approved" not in result.get("message", "").lower():
            log_test("Story Approval", False, "Unexpected approval response", result)
            return False
        
        log_test("Story Approval", True, "Story approved successfully by admin")
        return True
        
    except json.JSONDecodeError:
        log_test("Story Approval", False, "Invalid JSON response", response.text)
        return False

def test_public_stories():
    """Test retrieving public (approved) stories"""
    print("\n🧪 Testing Public Stories Retrieval...")
    
    # No authentication needed for public stories
    response, error = make_request("GET", "/stories/public", expected_status=200)
    
    if error:
        log_test("Public Stories", False, "Failed to retrieve public stories", error)
        return False
    
    try:
        stories = response.json()
        if not isinstance(stories, list):
            log_test("Public Stories", False, "Response should be a list")
            return False
        
        # Check if our approved story is now public
        found_approved = False
        for story in stories:
            if story["id"] == story_id and story["status"] == "approved":
                found_approved = True
                break
        
        if not found_approved:
            log_test("Public Stories", False, "Our approved story not found in public stories")
            return False
        
        log_test("Public Stories", True, f"Retrieved {len(stories)} public stories, including our approved story")
        return True
        
    except json.JSONDecodeError:
        log_test("Public Stories", False, "Invalid JSON response", response.text)
        return False

def test_story_like():
    """Test liking a story"""
    print("\n🧪 Testing Story Like Functionality...")
    
    if not user_token or not story_id:
        log_test("Story Like", False, "Missing user token or story ID")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response, error = make_request("POST", f"/stories/{story_id}/like", headers=headers, expected_status=200)
    
    if error:
        log_test("Story Like", False, "Story like failed", error)
        return False
    
    try:
        result = response.json()
        if "liked" not in result.get("message", "").lower():
            log_test("Story Like", False, "Unexpected like response", result)
            return False
        
        if "likes" not in result:
            log_test("Story Like", False, "Missing likes count in response")
            return False
        
        likes_count = result["likes"]
        log_test("Story Like", True, f"Story liked successfully, total likes: {likes_count}")
        return True
        
    except json.JSONDecodeError:
        log_test("Story Like", False, "Invalid JSON response", response.text)
        return False

def test_story_unlike():
    """Test unliking a story"""
    print("\n🧪 Testing Story Unlike Functionality...")
    
    if not user_token or not story_id:
        log_test("Story Unlike", False, "Missing user token or story ID")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response, error = make_request("POST", f"/stories/{story_id}/like", headers=headers, expected_status=200)
    
    if error:
        log_test("Story Unlike", False, "Story unlike failed", error)
        return False
    
    try:
        result = response.json()
        if "unliked" not in result.get("message", "").lower():
            log_test("Story Unlike", False, "Unexpected unlike response", result)
            return False
        
        if "likes" not in result:
            log_test("Story Unlike", False, "Missing likes count in response")
            return False
        
        likes_count = result["likes"]
        log_test("Story Unlike", True, f"Story unliked successfully, total likes: {likes_count}")
        return True
        
    except json.JSONDecodeError:
        log_test("Story Unlike", False, "Invalid JSON response", response.text)
        return False

def test_invalid_token():
    """Test API with invalid token"""
    print("\n🧪 Testing Invalid Token Handling...")
    
    headers = {"Authorization": "Bearer invalid_token_here"}
    response, error = make_request("GET", "/auth/me", headers=headers)
    
    if not response:
        log_test("Invalid Token Handling", False, "Request failed", error)
        return False
    
    if response.status_code == 401:
        log_test("Invalid Token Handling", True, "Correctly rejected invalid token")
        return True
    else:
        log_test("Invalid Token Handling", False, f"Expected 401, got {response.status_code}")
        return False

def run_all_tests():
    """Run all backend tests in sequence"""
    print("🚀 Starting Backend API Tests for Story Publishing Platform")
    print("=" * 70)
    
    tests = [
        # Authentication Tests
        test_user_registration,
        test_duplicate_registration,
        test_user_login,
        test_admin_login,
        test_jwt_validation,
        test_invalid_token,
        
        # Story CRUD Tests
        test_story_creation,
        test_my_stories,
        
        # Admin Moderation Tests
        test_pending_stories_admin,
        test_pending_stories_user_forbidden,
        test_story_approval,
        
        # Public Stories Test
        test_public_stories,
        
        # Like System Tests
        test_story_like,
        test_story_unlike,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            log_test(test_func.__name__, False, f"Test crashed: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 70)
    print("🏁 TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Backend is working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed. Check the details above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)