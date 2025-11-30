from rest_framework.response import Response

def success(data, status=200):
    return Response({
        "status": "success",
        "data": data
    }, status=status)

def error(message, status=400):
    return Response({
        "status": "error",
        "message": message
    }, status=status)
