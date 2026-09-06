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
        response = self.client.put("/api/v1/auth/update-profile/", data=payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["first_name"], "NewFirst")
        self.assertIsNotNone(response.data["data"]["profile_picture"])

        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_picture.name.startswith("profile_pictures/"))

    def test_unauthenticated_profile_update(self):
        unauthenticated_client = APIClient()
        response = unauthenticated_client.put("/api/v1/auth/update-profile/", data={"first_name": "Hack"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
