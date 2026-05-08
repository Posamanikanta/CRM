from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import *

class Create_Candidate(serializers.ModelSerializer):
    class Meta:
        model=Signup
        fields='__all__'

class Form_submit(serializers.ModelSerializer):
    class Meta:
        model=Candidate_Form
        fields='__all__'

class Sign_in(serializers.Serializer):
    email=serializers.EmailField()
    password=serializers.CharField()
    def validate(self,data):
        email=data.get('email')
        password=data.get('password')
        try:
            employee=Signup.objects.get(email=email,password=password)
        except:
            raise ValidationError("INVALID EMAIL OR PASSWORD")
        data['employee']=employee
        return data
    

class Admin_Sign_in(serializers.Serializer):
    email=serializers.EmailField()
    password=serializers.CharField()
    def validate(self,data):
        email=data.get('email')
        password=data.get('password')
        try:
            employee=Admin.objects.get(email=email,password=password)
        except:
            raise ValidationError("INVALID EMAIL OR PASSWORD")
        data['employee']=employee
        return data
    
class Super_Admin_Sign_in(serializers.Serializer):
    email=serializers.EmailField()
    password=serializers.CharField()
    def validate(self,data):
        email=data.get('email')
        password=data.get('password')
        try:
            employee=SuperAdmin.objects.get(email=email,password=password)
        except:
            raise ValidationError("INVALID EMAIL OR PASSWORD")
        data['employee']=employee
        return data