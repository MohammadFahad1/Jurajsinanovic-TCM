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


from unittest.mock import patch, MagicMock

class StripePaymentAPITestCase(TestCase):
    def setUp(self):
        from accounts.models import Plan, Payment
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="paymentuser@example.com",
            password="TestPassword123!",
            first_name="Payment",
            last_name="User",
            is_active=True
        )
        self.client.force_authenticate(user=self.user)
        self.plan = Plan.objects.create(
            name="Pro Monthly",
            billing_period="monthly",
            price=29.99,
            duration=30,
            active=True,
            order=1
        )

    @patch("stripe.checkout.Session.create")
    def test_create_checkout_session(self, mock_session_create):
        from accounts.models import Payment
        mock_session_create.return_value = MagicMock(
            id="cs_test_12345",
            url="https://checkout.stripe.com/pay/cs_test_12345"
        )

        response = self.client.post(f"/api/v1/auth/create-checkout-session/{self.plan.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["checkout_url"], "https://checkout.stripe.com/pay/cs_test_12345")

        payment = Payment.objects.filter(user=self.user, plan=self.plan).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, Payment.PENDING)
        self.assertEqual(payment.transaction_id, "cs_test_12345")

    @patch("stripe.Webhook.construct_event")
    def test_stripe_webhook_checkout_completed(self, mock_construct_event):
        from accounts.models import Payment
        pending_payment = Payment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=self.plan.price,
            payment_method="stripe",
            transaction_id="cs_test_99999",
            status=Payment.PENDING
        )

        mock_construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_99999",
                    "payment_intent": "pi_3MtwBwLkdIwHu7ix28a3tCGl",
                    "metadata": {
                        "user_id": self.user.id,
                        "plan_id": self.plan.id
                    }
                }
            }
        }

        response = self.client.post(
            "/api/v1/auth/stripe/webhook/",
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=signature"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pending_payment.refresh_from_db()
        self.assertEqual(pending_payment.status, Payment.SUCCESSFUL)
        self.assertEqual(pending_payment.transaction_id, "pi_3MtwBwLkdIwHu7ix28a3tCGl")

        self.user.refresh_from_db()
        self.assertEqual(self.user.plan, self.plan)
        self.assertEqual(self.user.status, User.ACTIVE)



