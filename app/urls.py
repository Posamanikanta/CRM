from django.urls import path
from .views import *

urlpatterns = [
   path('createaccount/', create_candidate),
   path('signin/',sign_in),
   path('formsubmit/',form_submit)

]