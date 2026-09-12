from rest_framework.response import Response
from health_check.models import Question, Answer
from health_check.serializers import QuestionSerializer, AnswerSerializer
from rest_framework import status
from core.base import NewAPIView, AutoPaginatedResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser

class QuestionListCreateView(NewAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['Health Check'], request_body=QuestionSerializer, responses={201: QuestionSerializer})
    def post(self, request, *args, **kwargs):
        """
        **Create a new question - Admin Only**\n
        This API is used for creating a new question.\n
        * Request Body:*
            - title: (string) Title or text of the question (required)
            - answers: (array) Array of answer objects (optional)
                - answer: (string) Answer text (required)
                - score: (integer) Answer score (default: 0)

        * Response:*
            - id: (integer) Question ID
            - title: (string) Question text / title
            - answers: (array) Array of answer objects
                - id: (integer) Answer ID
                - answer: (string) Answer text
                - score: (integer) Answer score
                - created_at: (string) Timestamp when answer was created
                - updated_at: (string) Timestamp when answer was last updated
            - option_count: (integer) Number of answer options associated with the question
            - created_at: (string) Timestamp when question was created
            - updated_at: (string) Timestamp when question was last updated

        **Example Request**\n
        ```json
        {
            "title": "How often do you feel tired during the day?",
            "answers": [
                {
                    "answer": "Rarely",
                    "score": 1
                },
                {
                    "answer": "Often",
                    "score": 2
                }
            ]
        }
        ```

        **Example Response**\n
        ```json
        {
            "id": 1,
            "title": "How often do you feel tired during the day?",
            "answers": [
                {
                    "id": 1,
                    "answer": "Rarely",
                    "score": 1,
                    "created_at": "2026-09-12T11:35:28.000Z",
                    "updated_at": "2026-09-12T11:35:28.000Z"
                },
                {
                    "id": 2,
                    "answer": "Often",
                    "score": 2,
                    "created_at": "2026-09-12T11:35:28.000Z",
                    "updated_at": "2026-09-12T11:35:28.000Z"
                }
            ],
            "option_count": 2,
            "created_at": "2026-09-12T11:35:28.000Z",
            "updated_at": "2026-09-12T11:35:28.000Z"
        }
        ```

        * Status Codes:*
            - 201: Question created successfully
            - 400: Bad request (e.g. missing required fields)
            - 403: Forbidden (Admin access required)
        """
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        return Response(self.get_serializer(question).data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(tags=['Health Check'], responses={200: QuestionSerializer(many=True)}, manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of items per page", type=openapi.TYPE_INTEGER),
        openapi.Parameter('search', openapi.IN_QUERY, description="Search query", type=openapi.TYPE_STRING),
        openapi.Parameter('order_by', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING, default='created_at'),
        openapi.Parameter('order_direction', openapi.IN_QUERY, description="Order direction", type=openapi.TYPE_STRING, default='desc'),
    ])
    def get(self, request, *args, **kwargs):
        """
        **Get a list of questions - Public**\n
        This API is used for retrieving a list of questions along with their associated answers.\n
        * Query Parameters:*
            - page: (integer) Page number (default: 1)
            - page_size: (integer) Number of items per page (default: 10)
            - search: (string) Search query to filter questions (optional)
            - order_by: (string) Field to order by (default: 'created_at')
            - order_direction: (string) Order direction ('asc' or 'desc', default: 'desc')
        
        * Response:*
            - success: (boolean) True if request was successful
            - pagination: (object) Pagination detail object
                - count: (integer) Total count of items
                - total_pages: (integer) Total number of pages
                - current_page: (integer) Current page number
                - next: (string|null) URL for the next page
                - previous: (string|null) URL for the previous page
            - results: (array) Array of question objects
                - id: (integer) Question ID
                - title: (string) Question text / title
                - answers: (array) Array of answer objects
                    - id: (integer) Answer ID
                    - answer: (string) Answer text
                    - score: (integer) Answer score
                    - created_at: (string) Timestamp when answer was created
                    - updated_at: (string) Timestamp when answer was last updated
                - option_count: (integer) Number of answer options associated with the question
                - created_at: (string) Timestamp when question was created
                - updated_at: (string) Timestamp when question was last updated

        **Example Response**\n
        ```json
        {
            "success": true,
            "pagination": {
                "count": 1,
                "total_pages": 1,
                "current_page": 1,
                "next": null,
                "previous": null
            },
            "results": [
                {
                    "id": 1,
                    "title": "How often do you feel tired during the day?",
                    "answers": [
                        {
                            "id": 1,
                            "answer": "Rarely",
                            "score": 1,
                            "created_at": "2026-09-12T11:35:28.000Z",
                            "updated_at": "2026-09-12T11:35:28.000Z"
                        }
                    ],
                    "option_count": 1,
                    "created_at": "2026-09-12T11:35:28.000Z",
                    "updated_at": "2026-09-12T11:35:28.000Z"
                }
            ]
        }
        ```

        * Status Codes:*
            - 200: Questions retrieved successfully
        """
        questions = Question.objects.prefetch_related('answers').all()
        serializer = self.get_serializer(questions, many=True)
        return AutoPaginatedResponse(serializer.data, request=request)

class QuestionDetailAPIView(NewAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'put', 'delete']

    def get_object(self, question_id=None):
        if question_id is None:
            question_id = self.kwargs.get('question_id') or self.kwargs.get('pk') or self.kwargs.get('id')
        try:
            return Question.objects.prefetch_related('answers').get(pk=question_id)
        except Question.DoesNotExist:
            return None

    @swagger_auto_schema(tags=['Health Check'], responses={200: QuestionSerializer()})
    def get(self, request, question_id=None, *args, **kwargs):
        """
        **Get a specific question by ID - Admin Only**\n
        This API is used for retrieving a specific question along with its associated answers.

        * Response:*
            - success: (boolean) True if request was successful
            - data: (object) Question object
                - id: (integer) Question ID
                - title: (string) Question text / title
                - answers: (array) Array of answer objects
                    - id: (integer) Answer ID
                    - answer: (string) Answer text
                    - score: (integer) Answer score
                    - created_at: (string) Timestamp when answer was created
                    - updated_at: (string) Timestamp when answer was last updated
                - option_count: (integer) Number of answer options associated with the question
                - created_at: (string) Timestamp when question was created
                - updated_at: (string) Timestamp when question was last updated

        **Example Response**\n
        ```json
        {
            "success": true,
            "data": {
                "id": 1,
                "title": "How often do you feel tired during the day?",
                "answers": [
                    {
                        "id": 1,
                        "answer": "Rarely",
                        "score": 1,
                        "created_at": "2026-09-12T11:35:28.000Z",
                        "updated_at": "2026-09-12T11:35:28.000Z"
                    }
                ],
                "option_count": 1,
                "created_at": "2026-09-12T11:35:28.000Z",
                "updated_at": "2026-09-12T11:35:28.000Z"
            }
        }
        ```

        * Status Codes:*
            - 200: Question retrieved successfully
            - 403: Forbidden (Admin access required)
            - 404: Question not found
        """
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        question = self.get_object(question_id=question_id)
        if not question:
            return Response({"success": False, "message": "Question not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(question)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(tags=['Health Check'], request_body=QuestionSerializer)
    def put(self, request, question_id=None, *args, **kwargs):
        """
        **Update a specific question by ID - Admin Only**\n
        This API is used for updating a specific question along with its associated answers.

        * Request:*
            - title: (string) Question text / title
            - answers: (array) Array of answer objects
                - answer: (string) Answer text
                - score: (integer) Answer score

        * Response:*
            - success: (boolean) True if request was successful
            - data: (object) Question object
                - id: (integer) Question ID
                - title: (string) Question text / title
                - answers: (array) Array of answer objects
                    - id: (integer) Answer ID
                    - answer: (string) Answer text
                    - score: (integer) Answer score
                    - created_at: (string) Timestamp when answer was created
                    - updated_at: (string) Timestamp when answer was last updated
                - option_count: (integer) Number of answer options associated with the question
                - created_at: (string) Timestamp when question was created
                - updated_at: (string) Timestamp when question was last updated

        **Example Response**\n
        ```json
        {
            "success": true,
            "data": {
                "id": 1,
                "title": "How often do you feel tired during the day?",
                "answers": [
                    {
                        "id": 1,
                        "answer": "Rarely",
                        "score": 1,
                        "created_at": "2026-09-12T11:35:28.000Z",
                        "updated_at": "2026-09-12T11:35:28.000Z"
                    }
                ],
                "option_count": 1,
                "created_at": "2026-09-12T11:35:28.000Z",
                "updated_at": "2026-09-12T11:35:28.000Z"
            }
        }
        ```

        * Status Codes:*
            - 200: Question updated successfully
            - 400: Bad request (Invalid data)
            - 403: Forbidden (Admin access required)
            - 404: Not found (Question not found)
        """
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        question = self.get_object(question_id=question_id)
        if not question:
            return Response({"success": False, "message": "Question not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(question, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        return Response({"success": True, "data": self.get_serializer(question).data}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(tags=['Health Check'], responses={200: "Success"})
    def delete(self, request, question_id=None, *args, **kwargs):
        """
        **Delete a specific question by ID - Admin Only**\n
        This API is used for deleting a specific question along with its associated answers.

        * Response:*
            - success: (boolean) True if request was successful
            - data: (string) Message indicating successful deletion

        **Example Response**\n
        ```json
        {
            "success": true,
            "data": "Question deleted successfully"
        }
        ```

        * Status Codes:*
            - 200: Question deleted successfully
            - 403: Forbidden (Admin access required)
            - 404: Not found (Question not found)
        """
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        question = self.get_object(question_id=question_id)
        if not question:
            return Response({"success": False, "message": "Question not found."}, status=status.HTTP_404_NOT_FOUND)
        question.delete()
        return Response({"success": True, "data": "Question deleted successfully"}, status=status.HTTP_200_OK)

