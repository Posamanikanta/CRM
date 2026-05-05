from django.urls import path
from .views import *

urlpatterns = [
   path('createaccount/', create_candidate),
   path('signin/',sign_in),
   path('formsubmit/',form_submit),
   path('candidates/',candidates),
   path('approval/<int:id>/',approval),
   path('approved_candidates/',approved_candidates_list),
   path('employee/<int:id>/',candidate_profile),
   path('employee-fee/<int:id>/',update_fee),
   path('add_payment/<int:id>/', add_payment),
   path('all_payments/', all_payments),
   path('interviews/', manage_interviews, name='manage_interviews'),



]