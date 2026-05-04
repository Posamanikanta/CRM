
from django.shortcuts import render, redirect

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from .serializers import *
from .models import Signup

@csrf_exempt
@api_view(['POST'])
def create_candidate(req):
        serializer=Create_Candidate(data=req.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        
@csrf_exempt
@api_view(['POST'])
def sign_in(req):
    serializer = Sign_in(data=req.data)
    serializer.is_valid(raise_exception=True)

    employee = serializer.validated_data['employee']
    emp_serializer = Create_Candidate(employee)

    return Response({
        "status": "success",
        'id':employee.id,
        "data": emp_serializer.data,
        "form_status": Candidate_Form.objects.filter(name=employee).first().status if Candidate_Form.objects.filter(name=employee).exists() else "form_pending"
    })

    
        
        
@csrf_exempt
@api_view(['POST'])
def form_submit(req):
    serializer = Form_submit(data=req.data)
    if serializer.is_valid():
        serializer.save(status="form_submitted")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

