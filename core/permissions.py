from django.contrib.auth import get_user_model
from rest_framework import permissions

User = get_user_model()

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user

    def has_permission(self, request, view):
        # Allow read-only access for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow write access only for authenticated users
        return request.user and request.user.is_authenticated
