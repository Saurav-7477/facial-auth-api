import cv2
import numpy as np
from celery import shared_task
from django.core.files.storage import default_storage
from deepface import DeepFace
from .models import UserProfile

@shared_task
def process_face_image(user_id, image_path):
    """Asynchronous task to process a face image"""
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return {"error": "Invalid image"}

        # Detect faces
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

        if len(faces) == 0:
            return {"error": "No face detected"}

        # Extract facial embeddings
        embedding = DeepFace.represent(image_path, model_name="Facenet")[0]["embedding"]

        # Store embedding
        user_profile, _ = UserProfile.objects.get_or_create(user_id=user_id)
        user_profile.face_embedding = embedding
        user_profile.profile_image = image_path
        user_profile.save()

        return {"message": "Face registered successfully"}
    except Exception as e:
        return {"error": str(e)}

@shared_task
def match_face(image_path):
    """Asynchronous task to match an uploaded face"""
    try:
        # Extract embedding from uploaded image
        uploaded_embedding = DeepFace.represent(image_path, model_name="Facenet")[0]["embedding"]

        # Retrieve registered users
        users = UserProfile.objects.exclude(face_embedding=None)

        best_match = None
        highest_similarity = 0.0

        for user_profile in users:
            stored_embedding = user_profile.face_embedding

            # Compute similarity (cosine distance)
            similarity = np.dot(stored_embedding, uploaded_embedding) / (np.linalg.norm(stored_embedding) * np.linalg.norm(uploaded_embedding))

            if similarity > highest_similarity and similarity > 0.85:  # Threshold for match
                best_match = user_profile.user
                highest_similarity = similarity

        if best_match:
            return {"message": f"Welcome, {best_match.username}!"}
        return {"error": "Face not recognized"}
    except Exception as e:
        return {"error": str(e)}
