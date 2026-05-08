from django.urls import path
from .views import *

urlpatterns = [
   path('createaccount/', create_candidate),
   path('signin/',sign_in),
   path('adminsignin/',admin_sign_in),
   path('superadminsignin/',super_admin_sign_in),
   path('formsubmit/',form_submit),
   path('candidates/',candidates),
   path('approval/<int:id>/',approval),
   path('approved_candidates/',approved_candidates_list),
   path('employee/<int:id>/',candidate_profile),
   path('employee-by-user/<int:id>/', candidate_profile_by_user),
   path('employee-fee/<int:id>/',update_fee),
   path('add_payment/<int:id>/', add_payment),
   path('all_payments/', all_payments),
   path('interviews/', manage_interviews, name='manage_interviews'),
   path('hiring-action/<int:id>/',hiring_stage_update, name='hiring_action'),
   path('update_candidate_status/<int:id>/', update_candidate_status, name='update_candidate_status'),
   path('send_offer/<int:pk>/', send_offer, name='send_offer'),
   path('add-expense/', add_expense, name='add_expense'),
   path('get-expenses/<int:admin_id>/', get_expenses, name='get_expenses'),
   path('get-all-expenses/',get_all_expenses, name='get_all_expenses'),
   path('candidate-stats/', candidate_stats, name='candidate_stats'),




]