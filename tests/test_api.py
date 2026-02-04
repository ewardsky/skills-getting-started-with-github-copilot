"""
Tests for the Mergington High School Activities API endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_dict(self, client):
        """Test that /activities returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_activities_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_get_activities_includes_chess_club(self, client):
        """Test that Chess Club is in the activities list"""
        response = client.get("/activities")
        activities = response.json()
        assert "Chess Club" in activities


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant(self, client):
        """Test signing up a new participant for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_list(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "alice@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]

    def test_signup_duplicate_participant_fails(self, client):
        """Test that signing up the same participant twice fails"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for a non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_participants(self, client):
        """Test that multiple different participants can sign up"""
        emails = ["student1@mergington.edu", "student2@mergington.edu"]
        for email in emails:
            response = client.post(f"/activities/Gym%20Class/signup?email={email}")
            assert response.status_code == 200
        
        response = client.get("/activities")
        gym_participants = response.json()["Gym Class"]["participants"]
        for email in emails:
            assert email in gym_participants


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self, client):
        """Test unregistering a participant who is signed up"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering a participant not in the activity fails"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notmember@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from a non-existent activity fails"""
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_then_resign_up(self, client):
        """Test that a participant can unregister and then sign up again"""
        email = "michael@mergington.edu"
        
        # Unregister
        response = client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        assert response.status_code == 200
        
        # Sign up again
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify in list
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complete user workflows"""

    def test_signup_and_unregister_workflow(self, client):
        """Test complete workflow: sign up, verify, unregister, verify removed"""
        email = "integration_test@mergington.edu"
        activity = "Programming%20Class"
        
        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        assert email in response.json()["Programming Class"]["participants"]
        
        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()["Programming Class"]["participants"]

    def test_multiple_activities_signup(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multi_activity@mergington.edu"
        activities = ["Chess%20Club", "Programming%20Class", "Gym%20Class"]
        
        # Sign up for multiple activities
        for activity in activities:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify in all activities
        response = client.get("/activities")
        data = response.json()
        for activity_key in ["Chess Club", "Programming Class", "Gym Class"]:
            assert email in data[activity_key]["participants"]
