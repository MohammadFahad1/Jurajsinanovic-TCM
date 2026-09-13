from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from health_check.models import Question, Answer, UserCheckIn, UserAnswer

User = get_user_model()

class UserCheckInAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="checkinuser@example.com",
            password="TestPassword123!",
            first_name="CheckIn",
            last_name="User",
            is_active=True
        )
        self.client.force_authenticate(user=self.user)
        
        self.question1 = Question.objects.create(title="How is your energy level?")
        self.answer1 = Answer.objects.create(question=self.question1, answer="High", score=10)
        self.answer2 = Answer.objects.create(question=self.question1, answer="Low", score=2)
        
        self.question2 = Question.objects.create(title="How many hours do you sleep?")
        self.answer3 = Answer.objects.create(question=self.question2, answer="8 Hours", score=8)

    def test_create_user_check_in(self):
        payload = {
            "answers": [
                {
                    "question": self.question1.id,
                    "answer": self.answer1.id
                },
                {
                    "question": self.question2.id,
                    "answer": self.answer3.id
                }
            ]
        }
        response = self.client.post("/api/v1/health_check/check-in/", data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "User check-in created successfully")
        self.assertEqual(response.data["data"]["status"], "completed")
        self.assertEqual(response.data["data"]["score"], 18)
        self.assertEqual(response.data["data"]["total_answered"], 2)
        self.assertEqual(response.data["data"]["pattern"], "Cold")
        self.assertEqual(len(response.data["data"]["answers"]), 2)
        self.assertEqual(response.data["data"]["answers"][0]["score"], 10)
        self.assertEqual(response.data["data"]["answers"][1]["score"], 8)

    def test_get_user_check_ins(self):
        check_in = UserCheckIn.objects.create(user=self.user, status=UserCheckIn.COMPLETED)
        UserAnswer.objects.create(check_in=check_in, question=self.question1, answer=self.answer1, score=10)

        response = self.client.get("/api/v1/health_check/check-in/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "User check-ins retrieved successfully")
        self.assertIsInstance(response.data["data"], list)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["id"], check_in.id)
        self.assertEqual(response.data["data"][0]["score"], 10)
        self.assertEqual(response.data["data"][0]["total_answered"], 1)
        self.assertEqual(response.data["data"][0]["pattern"], "Cold")

