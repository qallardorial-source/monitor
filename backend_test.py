#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import time

class SkiMonitorAPITester:
    def __init__(self, base_url="https://ski-appointments.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = "admin_session_1764880591104"
        self.test_user_token = None
        self.test_instructor_id = None
        self.test_lesson_id = None
        self.test_booking_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
            self.failed_tests.append({"test": name, "error": details})

    def make_request(self, method, endpoint, data=None, token=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            return success, response.json() if response.content else {}, response.status_code

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}, 0
        except json.JSONDecodeError:
            return False, {"error": "Invalid JSON response"}, response.status_code

    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        success, data, status = self.make_request('GET', 'health')
        self.log_test("Health endpoint", success and data.get('status') == 'healthy', 
                     f"Status: {status}, Response: {data}")
        return success

    def test_root_endpoint(self):
        """Test /api/ root endpoint"""
        success, data, status = self.make_request('GET', '')
        self.log_test("Root API endpoint", success and 'SkiMonitor' in data.get('message', ''), 
                     f"Status: {status}, Response: {data}")
        return success

    def test_instructors_list_empty(self):
        """Test /api/instructors GET (should be empty initially)"""
        success, data, status = self.make_request('GET', 'instructors')
        self.log_test("Instructors list (empty)", success and isinstance(data, list), 
                     f"Status: {status}, Count: {len(data) if isinstance(data, list) else 'N/A'}")
        return success

    def test_lessons_list_empty(self):
        """Test /api/lessons GET (should be empty initially)"""
        success, data, status = self.make_request('GET', 'lessons')
        self.log_test("Lessons list (empty)", success and isinstance(data, list), 
                     f"Status: {status}, Count: {len(data) if isinstance(data, list) else 'N/A'}")
        return success

    def test_admin_auth(self):
        """Test admin authentication"""
        success, data, status = self.make_request('GET', 'auth/me', token=self.admin_token)
        if success and data.get('role') == 'admin':
            self.log_test("Admin authentication", True)
            return True
        else:
            self.log_test("Admin authentication", False, f"Status: {status}, Role: {data.get('role')}")
            return False

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        success, data, status = self.make_request('GET', 'admin/stats', token=self.admin_token)
        expected_keys = ['total_users', 'total_instructors', 'pending_instructors', 'total_lessons', 'total_bookings']
        has_all_keys = all(key in data for key in expected_keys) if success else False
        self.log_test("Admin stats", success and has_all_keys, 
                     f"Status: {status}, Keys: {list(data.keys()) if success else 'N/A'}")
        return success

    def test_admin_pending_instructors(self):
        """Test admin pending instructors endpoint"""
        success, data, status = self.make_request('GET', 'admin/pending-instructors', token=self.admin_token)
        self.log_test("Admin pending instructors", success and isinstance(data, list), 
                     f"Status: {status}, Count: {len(data) if isinstance(data, list) else 'N/A'}")
        return success

    def create_test_user_session(self):
        """Create a test user session in MongoDB for testing"""
        try:
            import subprocess
            timestamp = int(time.time())
            user_id = f"test-user-{timestamp}"
            session_token = f"test_session_{timestamp}"
            
            mongo_script = f"""
            use('test_database');
            var userId = '{user_id}';
            var sessionToken = '{session_token}';
            db.users.insertOne({{
              id: userId,
              email: 'test.user.{timestamp}@example.com',
              name: 'Test User',
              picture: 'https://via.placeholder.com/150',
              role: 'client',
              created_at: new Date()
            }});
            db.user_sessions.insertOne({{
              user_id: userId,
              session_token: sessionToken,
              expires_at: new Date(Date.now() + 7*24*60*60*1000),
              created_at: new Date()
            }});
            print('Created user: ' + userId);
            print('Created session: ' + sessionToken);
            """
            
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.test_user_token = session_token
                print(f"  Created test session: {session_token}")
                self.log_test("Create test user session", True)
                return True
            else:
                self.log_test("Create test user session", False, f"MongoDB error: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_test("Create test user session", False, f"Error: {str(e)}")
            return False

    def test_user_auth(self):
        """Test user authentication with created session"""
        if not self.test_user_token:
            self.log_test("User authentication", False, "No test user token available")
            return False
            
        success, data, status = self.make_request('GET', 'auth/me', token=self.test_user_token)
        self.log_test("User authentication", success and data.get('role') == 'client', 
                     f"Status: {status}, Role: {data.get('role')}")
        return success

    def test_create_instructor(self):
        """Test creating instructor profile"""
        if not self.test_user_token:
            self.log_test("Create instructor", False, "No test user token available")
            return False
            
        instructor_data = {
            "bio": "Moniteur de ski expérimenté avec 10 ans d'expérience",
            "specialties": ["Ski alpin", "Snowboard"],
            "ski_levels": ["Débutant", "Intermédiaire", "Avancé"],
            "hourly_rate": 60.0
        }
        
        success, data, status = self.make_request('POST', 'instructors', instructor_data, self.test_user_token, 200)
        if success and data.get('id'):
            self.test_instructor_id = data['id']
            self.log_test("Create instructor", True)
            return True
        else:
            self.log_test("Create instructor", False, f"Status: {status}, Response: {data}")
            return False

    def test_approve_instructor(self):
        """Test admin approving instructor"""
        if not self.test_instructor_id:
            self.log_test("Approve instructor", False, "No test instructor ID available")
            return False
            
        approval_data = {"status": "approved"}
        success, data, status = self.make_request('PUT', f'instructors/{self.test_instructor_id}/status', 
                                                 approval_data, self.admin_token)
        self.log_test("Approve instructor", success, f"Status: {status}, Response: {data}")
        return success

    def test_create_lesson(self):
        """Test creating a lesson by approved instructor"""
        if not self.test_user_token:
            self.log_test("Create lesson", False, "No test user token available")
            return False
            
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        lesson_data = {
            "lesson_type": "private",
            "title": "Cours de ski particulier",
            "description": "Cours de ski pour débutant",
            "date": tomorrow,
            "start_time": "10:00",
            "end_time": "11:00",
            "max_participants": 1,
            "price": 60.0
        }
        
        success, data, status = self.make_request('POST', 'lessons', lesson_data, self.test_user_token, 200)
        if success and data.get('id'):
            self.test_lesson_id = data['id']
            self.log_test("Create lesson", True)
            return True
        else:
            self.log_test("Create lesson", False, f"Status: {status}, Response: {data}")
            return False

    def test_book_lesson(self):
        """Test booking a lesson"""
        if not self.test_lesson_id or not self.test_user_token:
            self.log_test("Book lesson", False, "Missing lesson ID or user token")
            return False
            
        booking_data = {
            "lesson_id": self.test_lesson_id,
            "participants": 1
        }
        
        success, data, status = self.make_request('POST', 'bookings', booking_data, self.test_user_token, 200)
        if success and data.get('id'):
            self.test_booking_id = data['id']
            self.log_test("Book lesson", True)
            return True
        else:
            self.log_test("Book lesson", False, f"Status: {status}, Response: {data}")
            return False

    def test_stripe_checkout(self):
        """Test Stripe checkout session creation"""
        if not self.test_booking_id or not self.test_user_token:
            self.log_test("Stripe checkout", False, "Missing booking ID or user token")
            return False
            
        payment_data = {
            "booking_id": self.test_booking_id,
            "origin_url": "https://ski-appointments.preview.emergentagent.com"
        }
        
        success, data, status = self.make_request('POST', 'payments/checkout', payment_data, self.test_user_token, 200)
        has_url = success and 'url' in data and 'session_id' in data
        self.log_test("Stripe checkout", has_url, f"Status: {status}, Has URL: {has_url}")
        return has_url

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 Starting SkiMonitor API Tests")
        print("=" * 50)
        
        # Basic API tests
        self.test_health_endpoint()
        self.test_root_endpoint()
        self.test_instructors_list_empty()
        self.test_lessons_list_empty()
        
        # Admin tests
        self.test_admin_auth()
        self.test_admin_stats()
        self.test_admin_pending_instructors()
        
        # User workflow tests
        self.create_test_user_session()
        self.test_user_auth()
        self.test_create_instructor()
        self.test_approve_instructor()
        self.test_create_lesson()
        self.test_book_lesson()
        self.test_stripe_checkout()
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run}")
        
        if self.failed_tests:
            print("\n❌ Failed tests:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['error']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = SkiMonitorAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())