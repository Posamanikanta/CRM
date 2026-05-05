
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
    employees = Candidate_Form.objects.filter(status="approved")
    serializer = Form_submit(employees, many=True)
    return Response(serializer.data)

import traceback
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
from rest_framework import status
# from django.shortcuts import get_object_or_404
# from .models import Candidate_Form

from django.db.models import Sum  # <--- CRITICAL: Make sure this is here!


@api_view(['GET'])
def candidate_profile(request, id):
    try:
        candidate = Candidate_Form.objects.get(id=id)

        # 1. Safely check for the resume file
        resume_url = None
        if candidate.resume and hasattr(candidate.resume, 'url'):
            try:
                resume_url = candidate.resume.url
            except ValueError:
                resume_url = None

        # 2. Fetch the individual payment records
        payments_data = candidate.payment_set.all().values(
            'id', 'amount', 'payment_date', 'screenshot'
        )

        # 3. SAFELY Calculate the totals
        # Get the sum, default to 0.00 if it returns None
        total_paid_dict = candidate.payment_set.aggregate(total=Sum('amount'))
        total_paid = float(total_paid_dict['total'] or 0.00)
        
        # Safely get the fee, default to 150000.00 if it's blank/None
        fee = float(candidate.fee or 150000.00)
        
        # Calculate balance
        balance = fee - total_paid

        # 4. Build the dictionary
        data = {
            "name": {
                "id": candidate.id,
                "name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone,
                "status": candidate.status,
                "resume": resume_url,
                "fee": fee,
                "total_paid": total_paid,
                "balance": balance
            },
            "payments": list(payments_data)
        }

        return Response(data, status=status.HTTP_200_OK)

    except Candidate_Form.DoesNotExist:
        return Response({"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        # If it crashes again, this will print the exact line and reason to your terminal!
        print("\n--- CRITICAL BACKEND ERROR ---")
        traceback.print_exc()
        print("------------------------------\n")
        return Response({"error": f"Server crash: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
        
        # We start by checking if a date was provided.
        # If yes, we filter immediately. If no, we return everything.
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
        # Check your terminal for the detailed error message
        print("--- DEBUG ERROR ---")
        traceback.print_exc() 
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



from django.shortcuts import get_object_or_404
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from .models import Candidate_Form, Interview


@api_view(['GET', 'POST'])
def manage_interviews(request):
    # --- GET: Fetch candidates with status 'approved' ---
    if request.method == 'GET':
        candidates = Candidate_Form.objects.filter(status='approved')
        data = [
            {"id": c.id, "full_name": c.full_name} 
            for c in candidates
        ]
        return Response(data)

    # --- POST: Save New Interview & Update Status ---
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
            # Automatically flip status to 'interview completed'
            candidate.status = "interview sheduled"
            candidate.save()

            return Response({
                "message": f"Interview scheduled and status updated for {candidate.full_name}!"
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("--- INTERVIEW SCHEDULING ERROR ---")
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


@api_view(['POST'])
def update_candidate_status(request, id):
    candidate = get_object_or_404(Candidate_Form, id=id)
    new_status = request.data.get('status')
    
    if new_status:
        candidate.status = new_status
        candidate.save()
        return Response({"message": "Status updated successfully"})
        
    return Response({"error": "No status provided"}, status=400)