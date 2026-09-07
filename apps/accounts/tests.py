from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class UpdateUserProfileAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="TestPassword123!",
            first_name="OriginalFirst",
            last_name="OriginalLast",
            is_active=True
        )
        self.client.force_authenticate(user=self.user)

    def test_update_name_via_me_put(self):
        payload = {
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast"
        }
        response = self.client.put("/api/v1/auth/me/", data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["first_name"], "UpdatedFirst")
        self.assertEqual(response.data["data"]["last_name"], "UpdatedLast")

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "UpdatedFirst")
        self.assertEqual(self.user.last_name, "UpdatedLast")

    def test_update_profile_picture_via_update_profile_put(self):
        from io import BytesIO
        from PIL import Image
        image_file = BytesIO()
        image = Image.new("RGB", (50, 50), color="blue")
        image.save(image_file, "JPEG")
        image_file.seek(0)
        uploaded_image = SimpleUploadedFile("avatar.jpg", image_file.read(), content_type="image/jpeg")

        payload = {
            "first_name": "NewFirst",
            "last_name": "NewLast",
            "profile_picture": uploaded_image
        }
        response = self.client.put("/api/v1/auth/me/", data=payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["first_name"], "NewFirst")
        self.assertIsNotNone(response.data["data"]["profile_picture"])

        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_picture.name.startswith("profile_pictures/"))

    def test_unauthenticated_profile_update(self):
        unauthenticated_client = APIClient()
        response = unauthenticated_client.put("/api/v1/auth/me/", data={"first_name": "Hack"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PlanUpdateTestCase(TestCase):
    def setUp(self):
        from accounts.models import Plan, PlanFeature
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPassword123!",
            first_name="Admin",
            last_name="User"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.plan = Plan.objects.create(
            name="Trial",
            billing_period="trial",
            price=0,
            duration=14,
            active=True,
            discount_note="Free Trial",
            order=1
        )
        PlanFeature.objects.create(plan=self.plan, feature="Old feature 1")

    def test_plan_serializer_update(self):
        from accounts.serializers import PlanSerializer
        serializer = PlanSerializer(
            instance=self.plan,
            data={
                "name": "Trial Updated",
                "billing_period": "trial",
                "price": 0,
                "duration": 14,
                "active": True,
                "discount_note": "Free Trial",
                "order": 1,
                "features": [
                    {"feature": "Full 24-question constitution assessment"},
                    {"feature": "Personalized organ & element insights"}
                ]
            },
            partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_plan = serializer.save()
        self.assertEqual(updated_plan.name, "Trial Updated")
        features = list(updated_plan.features.values_list("feature", flat=True))
        self.assertEqual(len(features), 2)
        self.assertIn("Full 24-question constitution assessment", features)

    def test_plan_update_api_view(self):
        payload = {
            "name": "Trial API",
            "billing_period": "trial",
            "price": 0,
            "duration": 14,
            "active": True,
            "discount_note": "Free Trial",
            "order": 1,
            "features": [
                {"feature": "Feature 1"},
                {"feature": "Feature 2"}
            ]
        }
        response = self.client.put(f"/api/v1/auth/plan/{self.plan.id}/", data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Plan updated successfully")


class PlanFeatureAPITestCase(TestCase):
    def setUp(self):
        from accounts.models import Plan, PlanFeature
        self.admin = User.objects.create_superuser(
            email="admin2@example.com",
            password="AdminPassword123!",
            first_name="Admin",
            last_name="User"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.plan = Plan.objects.create(
            name="Pro Plan",
            billing_period="monthly",
            price=29.99,
            duration=30,
            active=True,
            order=1
        )
        self.feature = PlanFeature.objects.create(plan=self.plan, feature="Initial Feature")

    def test_plan_feature_list(self):
        response = self.client.get("/api/v1/auth/plan-feature/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIsInstance(response.data["data"], list)
        self.assertEqual(len(response.data["data"]), 1)

    def test_plan_feature_create(self):
        payload = {
            "plan": self.plan.id,
            "feature": "New Created Feature"
        }
        response = self.client.post("/api/v1/auth/plan-feature/", data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["feature"], "New Created Feature")
        self.assertEqual(response.data["data"]["plan"], self.plan.id)

    def test_plan_feature_detail(self):
        response = self.client.get(f"/api/v1/auth/plan-feature/{self.feature.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["feature"], "Initial Feature")

    def test_plan_feature_update(self):
        payload = {
            "feature": "Updated Feature Name"
        }
        response = self.client.put(f"/api/v1/auth/plan-feature/{self.feature.id}/", data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["feature"], "Updated Feature Name")

    def test_plan_feature_delete(self):
        response = self.client.delete(f"/api/v1/auth/plan-feature/{self.feature.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Plan feature deleted successfully")


