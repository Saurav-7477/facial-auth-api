from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
import cv2
import numpy as np
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from .models import UserProfile
from .serializers import UserProfileSerializer
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings

from .tasks import process_face_image, match_face
from celery.result import AsyncResult

class FaceUploadView(APIView):
    """API to upload and process face images asynchronously"""

    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "No image uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        file_path = default_storage.save(f"temp/{image_file.name}", image_file)

        # Send image processing task to Celery
        process_face_image.delay(request.user.id, file_path)

        return Response({"message": "Face processing started"}, status=status.HTTP_202_ACCEPTED)


class FaceLoginView(APIView):
    """API to authenticate users via face recognition asynchronously"""

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "No image uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        file_path = default_storage.save(f"temp/{image_file.name}", image_file)

        # Process face matching asynchronously
        task = match_face.delay(file_path)

        return Response({"message": "Face matching in progress", "task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class FaceLoginStatusView(APIView):
    """Check the status of the face recognition task"""

    def get(self, request, task_id):
        task_result = AsyncResult(task_id)

        if task_result.state == "PENDING":
            return Response({"status": "Pending", "message": "Face matching is still in progress"}, status=status.HTTP_202_ACCEPTED)
        elif task_result.state == "SUCCESS":
            return Response(task_result.result, status=status.HTTP_200_OK)
        elif task_result.state == "FAILURE":
            return Response({"status": "Failed", "error": str(task_result.result)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"status": "Unknown"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegisterView(APIView):
    """API to handle user registration"""
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({"message": f"Hello {request.user.username}, you are authenticated!"})
