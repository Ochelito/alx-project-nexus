from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit/delete it.
    Assumes model has `.user` foreign key.
    """
    def has_object_permission(self, request, view, obj):
        # Read-only allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(obj, "user") and obj.user == request.user
