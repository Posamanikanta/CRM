
from django.shortcuts import render, redirect

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from .serializers import *
from .models import *

@csrf_exempt
@api_view(['POST'])
def create_candidate(req):
    serializer = Create_Candidate(data=req.data)
    
    # 1. If data is perfect, save and return success
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    # 2. FIXED: If data is invalid, return a 400 Bad Request with the exact errors!
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


@csrf_exempt
@api_view(['POST'])
def admin_sign_in(req):
    serializer = Admin_Sign_in(data=req.data)
    serializer.is_valid(raise_exception=True)
    employee = serializer.validated_data['employee']
    return Response({
        "message": "success",
        "id": employee.id,
        "name": employee.name,
        "email": employee.email

    }, status=status.HTTP_200_OK)





@csrf_exempt
@api_view(['POST'])
def super_admin_sign_in(req):
    serializer = Super_Admin_Sign_in(data=req.data)
    serializer.is_valid(raise_exception=True)
    employee = serializer.validated_data['employee']
    return Response({
        "message": "success",
        "id": employee.id,
        "name": employee.name,
        "email": employee.email

    }, status=status.HTTP_200_OK)


from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .models import Candidate_Form

@api_view(['GET'])
def candidate_stats(request):
    try:
        # 1. Pending: Matches 'pending' or 'form_pending'
        pending_count = Candidate_Form.objects.filter(status__icontains='pending').count()
        
        # 2. Rejected: Matches 'reject' or 'rejected'
        rejected_count = Candidate_Form.objects.filter(status__icontains='reject').count()

        # 3. Accepted: Excludes anyone who is pending OR rejected
        # This automatically captures 'approved', 'interview scheduled', 'offer released', etc.
        accepted_count = Candidate_Form.objects.exclude(
            Q(status__icontains='form_submitted') | Q(status__icontains='rejected')
        ).count()

        return Response({
            "status": "success",
            "counts": {
                "pending": pending_count,
                "accepted": accepted_count,
                "rejected": rejected_count
            }
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@csrf_exempt
@api_view(['POST'])
def sign_in(req):
    serializer = Sign_in(data=req.data)
    serializer.is_valid(raise_exception=True)

    employee = serializer.validated_data['employee']
    emp_serializer = Create_Candidate(employee)
    
    # 1. Fetch the candidate form cleanly (avoids double database queries)
    candidate_form = Candidate_Form.objects.filter(name=employee).first()
    form_status = candidate_form.status if candidate_form else "form_pending"

    # 2. Build the base response
    response_data = {
        "status": "success",
        "id": employee.id,
        "data": emp_serializer.data,
        "form_status": form_status,
        "interview_details": None # Default to None if not scheduled
    }

    # 3. If an interview is scheduled, fetch the details and add them to the response
    if candidate_form and form_status in ["interview sheduled", "interview scheduled"]:
        
        # Grab the latest interview associated with this candidate profile
        interview = Interview.objects.filter(name=candidate_form).last()
        
        if interview:
            response_data["interview_details"] = {
                "date": interview.interview_date,
                "interviewer": interview.interviewer,
                "link": interview.link
            }

    # 4. Return the final payload
    return Response(response_data)

# @csrf_exempt
# @api_view(['POST'])
# def sign_in(req):
#     serializer = Sign_in(data=req.data)
#     serializer.is_valid(raise_exception=True)

#     employee = serializer.validated_data['employee']
#     emp_serializer = Create_Candidate(employee)
    

#     return Response({
#         "status": "success",
#         'id':employee.id,
#         "data": emp_serializer.data,
#         "form_status": Candidate_Form.objects.filter(name=employee).first().status if Candidate_Form.objects.filter(name=employee).exists() else "form_pending"
#     })

    
        





@api_view(['POST'])
def approval(request, id):
    try:
        candidate = Candidate_Form.objects.get(id=id)

        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {"error": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        candidate.status = new_status
        candidate.save()

        return Response(
            {
                "message": "Status updated successfully",
                "updated_status": candidate.status
            },
            status=status.HTTP_200_OK
        )

    except Candidate_Form.DoesNotExist:
        return Response(
            {"error": "Candidate not found"},
            status=status.HTTP_404_NOT_FOUND
        )



@csrf_exempt
@api_view(['POST'])
def form_submit(req):
    serializer = Form_submit(data=req.data)
    if serializer.is_valid():
        serializer.save(status="form_submitted")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET'])
def candidates(request):
    employees = Candidate_Form.objects.filter(status="form_submitted")
    serializer = Form_submit(employees, many=True)
    return Response(serializer.data)



@api_view(['GET'])
def approved_candidates_list(request):
    employees = Candidate_Form.objects.filter(status__in=["approved", "interview sheduled","interview completed","interview finished","offer_released","candidate joined"])
    serializer = Form_submit(employees, many=True)
    return Response(serializer.data)

import traceback
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
from rest_framework import status
# from django.shortcuts import get_object_or_404
# from .models import Candidate_Form

from django.db.models import Sum  # <--- CRITICAL: Make sure this is here!



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Expense, Admin # Adjust import to match your app name
import json

@csrf_exempt # Use this if you aren't passing CSRF tokens via JS yet
def add_expense(request):
    if request.method == 'POST':
        try:
            # Extract data from FormData
            admin_id = request.POST.get('admin_id')
            amount = request.POST.get('amount')
            date_str = request.POST.get('date')
            category = request.POST.get('category')
            description = request.POST.get('description')
            photo = request.FILES.get('photo') # Handles the file upload

            # Find the admin
            admin_instance = Admin.objects.get(id=admin_id)

            # Create the expense in the database
            expense = Expense.objects.create(
                name=admin_instance, # Matches your ForeignKey field 'name'
                amount=amount,
                date=date_str,
                category=category,
                description=description,
                photo=photo
            )
            
            return JsonResponse({'status': 'success', 'message': 'Expense saved!'})
            
        except Admin.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Admin not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@csrf_exempt
def get_expenses(request, admin_id):
    if request.method == 'GET':
        try:
            # Get all expenses for this specific admin
            expenses = Expense.objects.filter(name__id=admin_id).order_by('-date')
            
            expense_list = []
            for exp in expenses:
                expense_list.append({
                    'id': exp.id,
                    'amount': float(exp.amount),
                    'date': exp.date.strftime('%Y-%m-%d'),
                    'category': exp.category,
                    'desc': exp.description,
                    # Check if photo exists before getting URL
                    'receipt': exp.photo.url if exp.photo else None 
                })
                
            return JsonResponse({'status': 'success', 'data': expense_list})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# @api_view(['GET'])
# def candidate_profile(request, id):
#     try:
#         candidate = Candidate_Form.objects.get(id=id)

#         # 1. Safely check for the resume file
#         resume_url = None
#         if candidate.resume and hasattr(candidate.resume, 'url'):
#             try:
#                 resume_url = candidate.resume.url
#             except ValueError:
#                 resume_url = None

#         # 2. Fetch the individual payment records
#         payments_data = candidate.payment_set.all().values(
#             'id', 'amount', 'payment_date', 'screenshot'
#         )

#         # 3. SAFELY Calculate the totals
#         # Get the sum, default to 0.00 if it returns None
#         total_paid_dict = candidate.payment_set.aggregate(total=Sum('amount'))
#         total_paid = float(total_paid_dict['total'] or 0.00)
        
#         # Safely get the fee, default to 150000.00 if it's blank/None
#         fee = float(candidate.fee or 150000.00)
        
#         # Calculate balance
#         balance = fee - total_paid

#         # 4. Build the dictionary
#         data = {
#             "name": {
#                 "id": candidate.id,
#                 "name": candidate.full_name,
#                 "email": candidate.email,
#                 "phone": candidate.phone,
#                 "status": candidate.status,
#                 "resume": resume_url,
#                 "fee": fee,
#                 "total_paid": total_paid,
#                 "balance": balance
#             },
#             "payments": list(payments_data)
#         }

#         return Response(data, status=status.HTTP_200_OK)

#     except Candidate_Form.DoesNotExist:
#         return Response({"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)
        
#     except Exception as e:
#         # If it crashes again, this will print the exact line and reason to your terminal!
#         print("\n--- CRITICAL BACKEND ERROR ---")
#         traceback.print_exc()
#         print("------------------------------\n")
#         return Response({"error": f"Server crash: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def candidate_profile(request, id):
    try:
        # id here = Candidate_Form.id (from admin)
        candidate = Candidate_Form.objects.filter(id=id).first()

        if not candidate:
            return Response(
                {"error": "Candidate not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Resume URL
        resume_url = None
        if candidate.resume and hasattr(candidate.resume, 'url'):
            try:
                resume_url = candidate.resume.url
            except ValueError:
                resume_url = None

        # Payments
        payments_qs   = candidate.payment_set.all()
        payments_data = list(payments_qs.values(
            'id', 'amount', 'payment_date', 'screenshot', 'bank_name'
        ))

        # Fix screenshot paths
        for p in payments_data:
            if p['screenshot']:
                p['screenshot'] = (
                    f"/media/{p['screenshot']}"
                    if not str(p['screenshot']).startswith('/media/')
                    else p['screenshot']
                )

        # Totals
        total_paid_dict = payments_qs.aggregate(total=Sum('amount'))
        total_paid      = float(total_paid_dict['total'] or 0.00)
        fee             = float(candidate.fee or 150000.00)
        balance         = fee - total_paid

        # Interview details
        interview_data = None
        interview = Interview.objects.filter(name=candidate).last()
        if interview:
            interview_data = {
                "date":        interview.interview_date,
                "interviewer": interview.interviewer,
                "link":        interview.link
            }

        data = {
            "name": {
                "id":         candidate.id,
                "signup_id":  candidate.name.id,
                "name":       candidate.full_name,
                "email":      candidate.email,
                "phone":      candidate.phone,
                "status":     candidate.status,
                "resume":     resume_url,
                "fee":        fee,
                "total_paid": total_paid,
                "balance":    balance
            },
            "interview_details": interview_data,
            "payments":          payments_data
        }

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        print("\n--- CRITICAL BACKEND ERROR ---")
        traceback.print_exc()
        print("------------------------------\n")
        return Response(
            {"error": f"Server crash: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
def update_fee(req,id):
    employee = Candidate_Form.objects.get(id=id)
    amount = req.data.get('amount')
    employee.fee = amount
    employee.save()
    return Response(
            {
                "message": "Status updated successfully",
                "updated_status": employee.fee
            },
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
def candidate_profile_by_user(request, id):
    try:
        # id here = Signup.id (from employee portal localStorage)
        candidate = Candidate_Form.objects.filter(name__id=id).first()

        if not candidate:
            return Response(
                {"error": "No form submitted yet"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Resume URL
        resume_url = None
        if candidate.resume and hasattr(candidate.resume, 'url'):
            try:
                resume_url = candidate.resume.url
            except ValueError:
                resume_url = None

        # Interview details
        interview_data = None
        interview = Interview.objects.filter(name=candidate).last()
        if interview:
            interview_data = {
                "date":        interview.interview_date,
                "interviewer": interview.interviewer,
                "link":        interview.link
            }

        data = {
            "name": {
                "id":     candidate.id,
                "name":   candidate.full_name,
                "email":  candidate.email,
                "phone":  candidate.phone,
                "status": candidate.status,
                "resume": resume_url,
            },
            "interview_details": interview_data,
        }

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        print("\n--- CRITICAL BACKEND ERROR ---")
        traceback.print_exc()
        print("------------------------------\n")
        return Response(
            {"error": f"Server crash: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def add_payment(request, id):
    try:
        # 1. Find the candidate
        candidate = Candidate_Form.objects.get(id=id)
        
        # 2. Get data from the request (including the file)
        amount = request.data.get('amount')
        bank_name = request.data.get('bank_name', '')
        screenshot = request.FILES.get('screenshot')

        if not amount:
            return Response({"error": "Payment amount is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Save to database
        new_payment = payment.objects.create(
            candidate=candidate,
            amount=amount,
            bank_name=bank_name,
            screenshot=screenshot
        )

        # 4. Return success and the new image URL
        return Response({
            "message": "Payment recorded successfully!",
            "payment": {
                "id": new_payment.id,
                "amount": new_payment.amount,
                "screenshot": new_payment.screenshot.url if new_payment.screenshot else None
            }
        }, status=status.HTTP_201_CREATED)

    except Candidate_Form.DoesNotExist:
        return Response({"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)
    


from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import payment
import traceback

@api_view(['GET'])
def all_payments(request):
    try:
        selected_date = request.query_params.get('date', None)
        if selected_date:
            payments_queryset = payment.objects.filter(payment_date__date=selected_date).select_related('candidate').order_by('-payment_date')
        else:
            payments_queryset = payment.objects.select_related('candidate').all().order_by('-payment_date')

        data = []
        for p in payments_queryset:
            data.append({
                "id": p.id,
                "candidate_name": p.candidate.full_name if p.candidate else "Unknown",
                "amount": float(p.amount),
                "bank_name": p.bank_name or "N/A",
                "payment_date": p.payment_date.strftime('%Y-%m-%d'), 
                "screenshot": p.screenshot.url if p.screenshot else None
            })
            
        return Response(data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print("--- DEBUG ERROR ---")
        traceback.print_exc() 
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



from django.shortcuts import get_object_or_404
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from .models import Candidate_Form, Interview


from django.core.mail import send_mail  # <-- Import this
from django.conf import settings        # <-- Import this

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from .models import Candidate_Form, Interview
import traceback
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from .models import Candidate_Form, Interview
import traceback

@api_view(['GET', 'POST'])
def manage_interviews(request):
    if request.method == 'GET':
        candidates = Candidate_Form.objects.filter(status='approved')
        data = [{"id": c.id, "full_name": c.full_name} for c in candidates]
        return Response(data)

    elif request.method == 'POST':
        try:
            candidate_id = request.data.get('candidate_id')
            interview_date = request.data.get('interview_date')
            interviewer = request.data.get('interviewer')
            meeting_link = request.data.get('link')

            # 1. Validation
            if not all([candidate_id, interview_date, interviewer, meeting_link]):
                return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Get the Candidate
            candidate = get_object_or_404(Candidate_Form, id=candidate_id)

            # 3. Create the Interview record
            Interview.objects.create(
                name=candidate,
                interview_date=interview_date,
                interviewer=interviewer,
                link=meeting_link
            )

            # 4. UPDATE CANDIDATE STATUS
            candidate.status = "interview sheduled"
            candidate.save()

            # 5. CONSTRUCT EMAIL CONTENT
            subject = 'Interview Scheduled - Oppty Tech'
            
            # Plain text fallback (for old email clients)
            plain_message = f"""
            Hi {candidate.full_name},
            
            Congratulations! Your profile has been approved, and we have officially scheduled an interview for you at Oppty Tech.
            
            Interview Details:
            Date: {interview_date}
            Interviewer: {interviewer}
            Link: {meeting_link}
            
            IMPORTANT INSTRUCTIONS:
            - Please join the meeting 15 minutes early.
            - Ensure your audio and video are turned ON for the duration of the interview.
            - Ensure you are connected to a high-speed, stable internet connection.
            
            Best regards,
            The Oppty HR Team
            """

            # HTML formatted version (Professional Styling with Disclaimer)
            html_message = f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                
                <!-- Header -->
                <div style="background-color: #ff6b00; color: #ffffff; padding: 25px 20px; text-align: center;">
                    <h2 style="margin: 0; font-size: 24px; letter-spacing: 0.5px;">Interview Scheduled</h2>
                </div>
                
                <!-- Body -->
                <div style="padding: 30px 20px; color: #334155; line-height: 1.6; background-color: #ffffff;">
                    <p style="font-size: 16px; margin-top: 0;">Hi <strong>{candidate.full_name}</strong>,</p>
                    <p style="font-size: 16px;">Congratulations! Your profile has been shortlisted, and we have officially scheduled an interview for you at Oppty Tech.</p>
                    
                    <!-- Details Card -->
                    <div style="background-color: #f8fafc; border-left: 4px solid #ff6b00; padding: 20px; border-radius: 6px; margin: 25px 0;">
                        <p style="margin: 5px 0; font-size: 15px;"><strong>📅 Date & Time:</strong> {interview_date}</p>
                        <p style="margin: 5px 0; font-size: 15px;"><strong>👤 Interviewer:</strong> {interviewer}</p>
                        
                    </div>
                    
                    <!-- Important Instructions/Disclaimer Box -->
                    <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 15px 20px; border-radius: 6px; margin: 25px 0;">
                        <h3 style="margin-top: 0; margin-bottom: 10px; color: #d97706; font-size: 16px;">⚠️ Important Instructions:</h3>
                        <ul style="padding-left: 20px; margin-bottom: 0; font-size: 14px; color: #78350f; line-height: 1.6;">
                            <li style="margin-bottom: 8px;"><strong>Punctuality:</strong> Please join the meeting <strong>15 minutes early</strong> to ensure there are no technical delays.</li>
                            <li style="margin-bottom: 8px;"><strong>Camera & Audio:</strong> Your audio and video must remain <strong>turned on</strong> for the entire duration of the interview.</li>
                            <li><strong>Connectivity:</strong> Please ensure you are connected to a <strong>high-speed, stable internet connection</strong>.</li>
                        </ul>
                    </div>
                    
                    <!-- Call to Action Button -->
                    <div style="text-align: center; margin: 35px 0;">
                        <a href="{meeting_link}" style="background-color: #05cd99; color: #ffffff; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block;">
                            Join Meeting
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: #64748b; margin-bottom: 0;">Let us know if you have any questions before your interview time. Good luck!</p>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f1f5f9; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0; font-size: 13px; color: #94a3b8;">Best regards,</p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; font-weight: bold; color: #64748b;">The Oppty HR Team</p>
                </div>
            </div>
            """
            
            # Send the email
            send_mail(
                subject=subject,
                message=plain_message,                 
                from_email=settings.DEFAULT_FROM_EMAIL, 
                recipient_list=[candidate.email],
                html_message=html_message,             
                fail_silently=False, 
            )

            return Response({
                "message": f"Interview scheduled and email sent to {candidate.full_name}!"
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("--- INTERVIEW SCHEDULING ERROR ---")
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




@api_view(['POST'])
def update_candidate_status(request, id):
    try:
        candidate = get_object_or_404(Candidate_Form, id=id)
        new_status = request.data.get('status')

        if not new_status:
            return Response({"error": "No status provided"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Update the candidate's status in the database
        candidate.status = new_status
        candidate.save()

        # 2. SEND THE EMAIL if they passed ("yes" or "interview completed")
        if new_status.lower() in ['yes', 'interview completed']:
            
            subject = 'Congratulations! Next Steps for Onboarding - Oppty Tech'
            
            # Plain text version (Fallback)
            plain_message = f"""Dear {candidate.full_name},

Congratulations!
We are pleased to inform you that you have successfully cleared all rounds of the interview process for the position of Associate Software Engineer (P3) at Oppty TechHub Pvt. Ltd.

As the next step in the onboarding process, we request you to share the following documents for verification:

- Aadhaar Card
- PAN Card
- 10th Standard Certificate
- 12th Standard Certificate
- Graduation Certificate
- Post-Graduation Certificate (if applicable)

Kindly ensure that the documents are clear and legible. Once we receive and verify the above documents, we will proceed with issuing your Offer Letter.

Please share the requested documents at your earliest convenience to help us move forward smoothly.

If you have any questions or require clarification, feel free to reach out.

We look forward to welcoming you to Oppty TechHub Pvt. Ltd."""

            # Beautiful HTML formatted version
            html_message = f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #334155; line-height: 1.6;">
                <p>Dear <strong>{candidate.full_name}</strong>,</p>
                
                <h3 style="color: #05cd99;">Congratulations!</h3>
                <p>We are pleased to inform you that you have successfully cleared all rounds of the interview process for the position of <strong>Associate Software Engineer (P3)</strong> at Oppty TechHub Pvt. Ltd.</p>
                
                <p>As the next step in the onboarding process, we request you to share the following documents for verification:</p>
                
                <ul style="background-color: #f8fafc; padding: 20px 40px; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <li style="margin-bottom: 8px;">Aadhaar Card</li>
                    <li style="margin-bottom: 8px;">PAN Card</li>
                    <li style="margin-bottom: 8px;">10th Standard Certificate</li>
                    <li style="margin-bottom: 8px;">12th Standard Certificate</li>
                    <li style="margin-bottom: 8px;">Graduation Certificate</li>
                    <li>Post-Graduation Certificate (if applicable)</li>
                </ul>
                
                <p>Kindly ensure that the documents are clear and legible. Once we receive and verify the above documents, we will proceed with issuing your Offer Letter.</p>
                
                <p>Please share the requested documents at your earliest convenience to help us move forward smoothly. If you have any questions or require clarification, feel free to reach out.</p>
                
                <br>
                <p style="margin-bottom: 0;">We look forward to welcoming you to,</p>
                <p style="margin-top: 5px; font-weight: bold; color: #ff6b00;">Oppty TechHub Pvt. Ltd.</p>
            </div>
            """

            # Send the email using Django's built-in mailer
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[candidate.email],
                html_message=html_message,
                fail_silently=False,
            )

        return Response({"message": f"Status updated to {new_status}"}, status=status.HTTP_200_OK)

    except Exception as e:
        print("--- STATUS UPDATE ERROR ---")
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
def hiring_stage_update(request, id):
    """
    Unified view to handle the Hiring Action state machine transitions:
    - approved -> interview sheduled
    - interview sheduled -> interview completed (if Yes)
    - interview sheduled -> approved (if No/Reschedule)
    """
    candidate = get_object_or_404(Candidate_Form, id=id)
    action = request.data.get('action') # 'schedule', 'complete', or 'reset'

    try:
        if action == 'schedule':
            # This logic transitions from Approved to Scheduled
            interview_date = request.data.get('interview_date')
            interviewer = request.data.get('interviewer')
            link = request.data.get('link')

            if not all([interview_date, interviewer, link]):
                return Response({"error": "Interview details are missing"}, status=400)

            # Create/Update Interview record
            Interview.objects.update_or_create(
                name=candidate,
                defaults={
                    'interview_date': interview_date,
                    'interviewer': interviewer,
                    'link': link
                }
            )
            candidate.status = "interview sheduled"
        
        elif action == 'complete':
            # This logic transitions from Scheduled to Completed (The 'Yes' button)
            candidate.status = "interview completed"
        
        elif action == 'reset':
            # This logic transitions from Scheduled back to Approved (The 'No' button)
            candidate.status = "approved"
        
        else:
            return Response({"error": "Invalid hiring action"}, status=400)

        candidate.save()
        return Response({
            "message": f"Candidate status is now {candidate.status}",
            "status": candidate.status
        }, status=status.HTTP_200_OK)

    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)





from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.mail import EmailMessage
from django.conf import settings
import os
import traceback
from .models import Candidate_Form, Offer # Adjust imports to your actual models

@api_view(['POST'])
def send_offer(request, pk):
    try:
        candidate = get_object_or_404(Candidate_Form, id=pk)

        # 1. Get the uploaded file and form data
        offer_file = request.FILES.get('offer_letter')
        position = request.data.get('position', 'Not Specified')
        salary = request.data.get('salary', '0')
        date_of_joining = request.data.get('date_of_joining', None)

        if not offer_file:
            return Response(
                {"error": "Please select an Offer Letter PDF to upload."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Remove old offers to prevent clutter
        old_offers = Offer.objects.filter(name=candidate)
        for old in old_offers:
            if old.offer_letter and os.path.exists(old.offer_letter.path):
                try:
                    os.remove(old.offer_letter.path)
                except:
                    pass
        old_offers.delete()

        # 3. Create the new Offer record and save the uploaded file
        offer = Offer.objects.create(
            name=candidate,
            joining_date=date_of_joining,
            position=position,
            salary=salary,
            offer_letter=offer_file # Saves the uploaded file directly
        )

        # 4. Update the candidate's hiring status
        candidate.status = "offer_released"
        candidate.save()

        # 5. Email the uploaded Offer Letter to the candidate
        email_subject = f"Offer of Employment - {position} at Oppty TechHub"
        email_body = f"""Dear {candidate.full_name},

Congratulations! We are thrilled to offer you the position of {position} at Oppty TechHub Pvt. Ltd.

Please find your official Offer Letter attached to this email.

We look forward to welcoming you to the team!

Best Regards,
HR Team
Oppty TechHub Pvt. Ltd."""

        email = EmailMessage(
            subject=email_subject,
            body=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[candidate.email],
        )
        email.attach_file(offer.offer_letter.path)
        email.send(fail_silently=False)

        return Response({
            "message": f"Offer Letter uploaded and sent to {candidate.email} successfully!",
            "offer_id": offer.id,
            "pdf_url": offer.offer_letter.url
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print("\n--- OFFER UPLOAD ERROR ---")
        traceback.print_exc()
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# def get_logo_base64():
#     """Load Oppty logo as base64."""
#     logo_path = os.path.join(settings.BASE_DIR, 'media', 'logo.png')
#     if os.path.exists(logo_path):
#         with open(logo_path, 'rb') as f:
#             # FIX: Use image/jpeg (not image/png) since the logo is a JPEG file
#             return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
#     return ""


# @api_view(['POST'])
# def send_offer(request, pk):
#     try:
#         candidate = get_object_or_404(Candidate_Form, id=pk)

#         # ── Request Data ─────────────────────────────────────────────────────
#         position        = request.data.get('position')
#         salary          = request.data.get('salary')
#         date_of_joining = request.data.get('date_of_joining')
#         salary_in_words = request.data.get('salary_in_words', '')
#         address         = request.data.get('address', '')

#         if not all([position, salary, date_of_joining]):
#             return Response(
#                 {"error": "Position, Salary and Date of Joining are required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # ── Date Formatting ──────────────────────────────────────────────────
#         now           = datetime.now()
#         current_date  = now.strftime('%d/%m/%Y')

#         # Agreement date: "23rd Feb 2026"
#         now_ord        = get_ordinal(now.day)
#         agreement_date = f"{now.day}{now_ord} {now.strftime('%b')} {now.year}"

#         # DOJ: "February 26th, 2026"
#         doj_obj        = datetime.strptime(date_of_joining, '%Y-%m-%d')
#         doj_ord        = get_ordinal(doj_obj.day)
#         formatted_doj  = f"{doj_obj.strftime('%B')} {doj_obj.day}{doj_ord}, {doj_obj.year}"

#         # ── CTC Display ──────────────────────────────────────────────────────
#         formatted_salary = format_indian_currency(salary)
#         ctc_display = f"&#8377;{formatted_salary} PA"
#         if salary_in_words:
#             ctc_display += f" ({salary_in_words})"

#         # ── Logo ─────────────────────────────────────────────────────────────
#         LOGO = get_logo_base64()

#         # ── HTML Template ────────────────────────────────────────────────────
#         html_content = f"""<!DOCTYPE html>
# <html>
# <head>
# <meta charset="UTF-8"/>
# <style>
#     @page {{
#         size: A4 portrait;
#         margin: 1.3cm 2cm 3.2cm 2cm;

#         @frame footer_frame {{
#             -pdf-frame-content: footerContent;
#             left: 2cm;
#             right: 2cm;
#             bottom: 0.8cm;
#             height: 2.3cm;
#         }}

#         @frame watermark_frame {{
#             -pdf-frame-content: watermarkContent;
#             left: 3cm;
#             top: 8cm;
#             width: 15cm;
#             height: 12cm;
#         }}
#     }}

#     body {{
#         font-family: Helvetica, Arial, sans-serif;
#         font-size: 11pt;
#         color: #000000;
#         line-height: 1.55;
#         margin: 0;
#         padding: 0;
#     }}

#     p {{
#         margin: 0 0 8pt 0;
#         text-align: justify;
#     }}

#     .logo-wrap {{
#         text-align: center;
#         margin-bottom: 16pt;
#     }}

#     .logo-wrap img {{
#         height: 70pt;
#     }}

#     .watermark {{
#         text-align: center;
#         opacity: 0.08;
#     }}

#     .watermark img {{
#         width: 380pt;
#     }}

#     .company-name {{
#         color: #E86C1F;
#         font-size: 17pt;
#         font-weight: bold;
#         margin: 0 0 8pt 0;
#     }}

#     .doc-title {{
#         text-align: center;
#         font-weight: bold;
#         text-decoration: underline;
#         font-size: 12pt;
#         margin: 16pt 0 14pt 0;
#     }}

#     .agreement-title {{
#         text-align: center;
#         font-weight: bold;
#         font-size: 12pt;
#         margin: 8pt 0 14pt 0;
#     }}

#     .sec-head {{
#         font-weight: bold;
#         font-size: 11pt;
#         margin: 12pt 0 4pt 0;
#     }}

#     .sig-line {{
#         border-bottom: 1pt solid #000000;
#         display: inline-block;
#         width: 170pt;
#         height: 14pt;
#     }}

#     .footer {{
#         text-align: center;
#         font-size: 9.5pt;
#         color: #000000;
#         line-height: 1.5;
#     }}

#     .footer p {{
#         margin: 1pt 0;
#         text-align: center;
#     }}

#     .f-orange {{
#         color: #E86C1F;
#         font-weight: bold;
#         font-size: 10.5pt;
#         margin-bottom: 3pt;
#     }}

#     .f-link {{
#         color: #0066cc;
#         text-decoration: underline;
#     }}

#     .page-break {{
#         page-break-after: always;
#     }}

#     .terms-list p {{
#         margin: 5pt 0;
#         text-align: left;
#     }}

#     .top-right {{
#         text-align: right;
#         font-weight: bold;
#         margin-top: 8pt;
#     }}

#     /* FIX: Two-column layout for To/address block vs Date */
#     .header-row {{
#         width: 100%;
#     }}
#     .header-row td {{
#         vertical-align: top;
#         padding: 0;
#     }}
#     .header-left {{
#         width: 65%;
#     }}
#     .header-right {{
#         width: 35%;
#         text-align: right;
#         font-weight: bold;
#     }}
# </style>
# </head>
# <body>

# <!-- ============== WATERMARK (Background) ============== -->
# <div id="watermarkContent">
#     <div class="watermark">
#         <img src="{LOGO}" alt=""/>
#     </div>
# </div>

# <!-- ============== FOOTER (Every Page) ============== -->
# <div id="footerContent">
#     <div class="footer">
#         <p class="f-orange">Oppty TechHub Pvt. Ltd.</p>
#         <p>H. No 2-108/43, 1st floor, Vijaya Lakshmi Enclave,</p>
#         <p>ICRISAT Colony, PJR Enclave Rd, Gangaram, Hyderabad, Telangana 500050</p>
#         <p>
#             <strong>Email:</strong>
#             <span class="f-link">info@Oppty.in</span>,
#             <strong>Website:</strong>
#             <span class="f-link">https://oppty.in</span>
#         </p>
#     </div>
# </div>


# <!-- ====================================================
#      PAGE 1 - OFFER LETTER
# ==================================================== -->

# <div class="logo-wrap">
#     <img src="{LOGO}" alt="Oppty TechHub"/>
# </div>

# <p class="company-name">Oppty TechHub Pvt. Ltd.</p>

# <p style="font-size:11pt; line-height:1.5; margin:0 0 4pt 0; text-align:left;">
#     <strong>Registered Office:</strong> H. NO: 2-108/43, 1st floor,<br/>
#     Vijaya Lakshmi Enclave, ICRISAT Colony, PJR<br/>
#     Enclave Rd, Gangaram, Hyderabad, Telangana<br/>
#     500050.<br/>
#     Email: <span class="f-link">info@Oppty.in</span>, Phone: 9491209900.
# </p>

# <p class="doc-title">OFFER LETTER</p>

# <!-- FIX: To/Address on LEFT, Date on RIGHT using table layout -->
# <table class="header-row" cellpadding="0" cellspacing="0">
#     <tr>
#         <td class="header-left">
#             <p style="margin:0;"><strong>To,</strong></p>
#             <p style="margin:0;"><strong>{candidate.full_name}</strong></p>
#             <p style="margin:0 0 14pt 0; text-align:left;">{address}</p>
#         </td>
#         <td class="header-right">
#             <p style="margin:0; text-align:right;">Date: {current_date}.</p>
#         </td>
#     </tr>
# </table>

# <p style="margin:14pt 0 6pt 0; text-align:center;">
#     <strong><u>Subject: Offer of Employment as {position}</u></strong>
# </p>

# <br/>

# <p>Dear <strong>{candidate.full_name},</strong></p>

# <p>
#     We are pleased to offer you the position of <strong>{position}</strong> at
#     <strong>Oppty Techhub Pvt Ltd.</strong>, effective from <strong>{formatted_doj}</strong>.
# </p>

# <p>Based on our discussions and your qualifications, here are the terms of your employment:</p>

# <br/>

# <div class="terms-list">
#     <p><strong>Job Title:</strong> {position}</p>
#     <p><strong>Department:</strong> IT</p>
#     <p><strong>Reporting To:</strong> K Chanukya Chowdary (HOD)</p>
#     <p><strong>Location:</strong> Hybrid</p>
#     <p><strong>CTC (Annual):</strong> {ctc_display}</p>
#     <p><strong>Probation Period:</strong> 3 months from the date of joining</p>
#     <p><strong>Working Hours:</strong> 10.00 AM &#8211; 07.00 PM, Monday to Saturday.</p>
# </div>

# <div class="page-break"></div>


# <!-- ====================================================
#      PAGE 2 - CONTINUATION + ACCEPTANCE
# ==================================================== -->

# <div class="logo-wrap">
#     <img src="{LOGO}" alt="Oppty TechHub"/>
# </div>

# <p>
#     You are expected to meet the responsibilities and duties assigned to you in
#     accordance with the company policies. This offer is contingent upon the
#     successful completion of background verification and submission of all
#     required documents.
# </p>

# <p>
#     Please confirm your acceptance of this offer by signing and returning the
#     enclosed copy of this letter. We look forward to your contributions and a
#     successful journey with <strong>Oppty TechHub Pvt. Ltd</strong>.
# </p>

# <br/><br/>

# <p style="margin:0;">Sincerely,</p>
# <p style="margin:0;"><strong>Shanti Priya,</strong></p>
# <p style="margin:0;">HR Manager,</p>
# <p style="margin:0;">Oppty TechHub Pvt. Ltd</p>

# <br/><br/>

# <p><strong>I Accept the Terms &amp; Conditions of the Offer</strong></p>

# <br/>

# <p style="margin:0;"><strong>Signature:</strong> <span class="sig-line">&nbsp;</span></p>
# <p style="margin:8pt 0 0 0;"><strong>Name:</strong>&nbsp; {candidate.full_name}</p>

# <div class="page-break"></div>


# <!-- ====================================================
#      PAGE 3 - EMPLOYMENT AGREEMENT
# ==================================================== -->

# <div class="logo-wrap">
#     <img src="{LOGO}" alt="Oppty TechHub"/>
# </div>

# <p class="agreement-title">EMPLOYMENT AGREEMENT</p>

# <p>
#     This Employment Agreement was made on this <strong>{agreement_date}</strong>,
#     between <strong>Oppty TechHub Pvt. Ltd.</strong>, a company incorporated
#     under the Companies Act, 2013, having its registered office at H. NO:
#     2-108/43, 1st floor, Vijaya Lakshmi Enclave, ICRISAT Colony, PJR Enclave Rd,
#     Gangaram, Hyderabad, Telangana 500050, (hereinafter referred to as the
#     &#8220;Company&#8221;), <strong>{candidate.full_name}</strong> {address}
#     (hereinafter referred to as the &#8220;Employee&#8221;).
# </p>

# <br/>

# <p class="sec-head">Position and Duties</p>
# <p>
#     The Employee agrees to serve as an <strong>{position}</strong> and shall
#     perform all duties assigned to them. The Employee shall comply with company
#     policies and report to the designated supervisor.
# </p>

# <p class="sec-head">Compensation</p>
# <p>
#     The Company shall pay a total annual CTC of <strong>{ctc_display}</strong>
#     subject to applicable taxes and statutory deductions.
# </p>

# <p class="sec-head">Working Hours</p>
# <p>The normal working hours are from 10:00 AM to 07:00 PM, Monday through Saturday.</p>

# <p class="sec-head">Confidentiality</p>
# <p>
#     The Employee agrees not to disclose any confidential information of the
#     company during or after employment without prior written consent.
# </p>

# <p class="sec-head">Intellectual Property</p>
# <p>Any work product developed during employment shall be the sole property of the Company.</p>

# <p class="sec-head">Termination</p>
# <p>
#     Either party may terminate this agreement by giving [30] days&#8217; written
#     notice or salary in lieu thereof. The company reserves the right to terminate
#     employment immediately in case of misconduct or policy violations.
# </p>

# <p>
#     If any company assets are in the name of the employee, they must be
#     re-submitted at the time of reliving (Like laptops, ID cards, etc).
# </p>

# <div class="page-break"></div>


# <!-- ====================================================
#      PAGE 4 - GOVERNING LAW + SIGNATURES
# ==================================================== -->

# <div class="logo-wrap">
#     <img src="{LOGO}" alt="Oppty TechHub"/>
# </div>

# <p class="sec-head">Governing Law</p>
# <p>
#     This agreement shall be governed by the laws of India and subject to the
#     jurisdiction of the courts of Hyderabad.
# </p>

# <br/>

# <p>
#     &#8220;IN WITNESS WHEREOF, the parties to this agreement have executed it as
#     of the date first written above.&#8221;
# </p>

# <br/><br/>

# <p style="margin:0;"><strong>For Oppty TechHub Pvt. Ltd.</strong></p>
# <p style="margin:0;"><strong>Signature:</strong> <strong>Shanti Priya</strong></p>
# <p style="margin:0;"><strong>Designation:</strong> <strong>HR Manager</strong></p>

# <br/><br/><br/>

# <p style="margin:0;"><strong>Employee</strong></p>
# <p style="margin:0;"><strong>Signature:</strong> <span class="sig-line">&nbsp;</span></p>
# <p style="margin:8pt 0 0 0;"><strong>Name:</strong>&nbsp; <strong>{candidate.full_name}</strong></p>
# <p style="margin:8pt 0 0 0;"><strong>Date:</strong>&nbsp; <strong>{current_date}</strong></p>

# </body>
# </html>"""

#         # ── Generate PDF ─────────────────────────────────────────────────────
#         pdf_buffer  = BytesIO()
#         pisa_status = pisa.CreatePDF(
#             BytesIO(html_content.encode("UTF-8")),
#             dest=pdf_buffer
#         )

#         if pisa_status.err:
#             return Response(
#                 {"error": "Failed to generate PDF."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#         # ── Save Offer to DB (delete old offers first) ────────────────────────
#         filename = f"{candidate.full_name.replace(' ', '_')}_Offer_Letter.pdf"

#         old_offers = Offer.objects.filter(name=candidate)
#         for old in old_offers:
#             if old.offer_letter and os.path.exists(old.offer_letter.path):
#                 try:
#                     os.remove(old.offer_letter.path)
#                 except:
#                     pass
#         old_offers.delete()

#         offer = Offer.objects.create(
#             name=candidate,
#             joining_date=date_of_joining,
#             position=position,
#             salary=salary
#         )

#         offer.offer_letter.save(
#             filename,
#             ContentFile(pdf_buffer.getvalue()),
#             save=True
#         )

#         # ── Update Status ─────────────────────────────────────────────────────
#         candidate.status = "offer_released"
#         candidate.save()

#         # ── Send Email ────────────────────────────────────────────────────────
#         email_subject = f"Offer of Employment - {position} at Oppty TechHub Pvt. Ltd."
#         email_body = f"""Dear {candidate.full_name},

# Congratulations! We are thrilled to offer you the position of {position} at Oppty TechHub Pvt. Ltd.

# Please find your official Offer Letter and Employment Agreement attached.

# Key Details:
#   Position        : {position}
#   CTC (Annual)    : Rs. {formatted_salary} PA
#   Date of Joining : {formatted_doj}

# We look forward to welcoming you to the team!

# Best Regards,
# Shanti Priya
# HR Manager
# Oppty TechHub Pvt. Ltd.
# Phone: 9491209900
# Email: info@Oppty.in"""

#         email = EmailMessage(
#             subject=email_subject,
#             body=email_body,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[candidate.email],
#         )
#         email.attach_file(offer.offer_letter.path)
#         email.send(fail_silently=False)

#         return Response(
#             {
#                 "message": f"Offer Letter sent to {candidate.email} successfully!",
#                 "offer_id": offer.id,
#                 "pdf_url":  offer.offer_letter.url
#             },
#             status=status.HTTP_201_CREATED
#         )

#     except Exception as e:
#         print("\n--- OFFER GENERATION ERROR ---")
#         traceback.print_exc()
#         return Response(
#             {"error": str(e)},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )