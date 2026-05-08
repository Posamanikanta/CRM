from django.db import models

class Signup(models.Model):
    name = models.CharField(max_length=100)
    email =models.EmailField()
    password = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Candidate_Form(models.Model):
    name = models.ForeignKey(Signup, on_delete=models.CASCADE)
    full_name=models.CharField(max_length=100)
    email =models.EmailField()
    phone = models.CharField(max_length=10)
    resume = models.FileField(upload_to='resumes/')
    applied_on = models.DateTimeField(auto_now_add=True)
    dob = models.DateField()
    refered = models.CharField(max_length=100, blank=True, null=True)
    experiences=models.CharField(max_length=30 ,default=0)
    passed_out=models.CharField(max_length=4)
    status = models.CharField(max_length=30,default="form_pending")
    fee = models.DecimalField(max_digits=10,null=True,blank=True, decimal_places=2)

    def __str__(self):
        return self.name.name
    


class Interview(models.Model):
    name = models.ForeignKey(Candidate_Form, on_delete=models.CASCADE)
    interview_date = models.DateTimeField()
    interviewer = models.CharField(max_length=100)
    link = models.URLField()

    def __str__(self):
        return f"Interview for {self.name.name} on {self.interview_date}"
    

class payment(models.Model):
    candidate = models.ForeignKey(Candidate_Form, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    screenshot = models.FileField(upload_to='screenshots/')
    bank_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Payment of {self.amount} for {self.candidate.name} on {self.payment_date}"



class Offer(models.Model):
    name = models.ForeignKey(Candidate_Form, on_delete=models.CASCADE)
    joining_date = models.DateTimeField()
    position = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    offer_letter = models.FileField(upload_to='offer_letters/') 
    
    def __str__(self):
        return f"Offer for {self.name.name} for position {self.position} with salary {self.salary}"
    


class Admin(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.name

from django.utils import timezone # Make sure to import this if you use timezone.now

class Expense(models.Model):
    name= models.ForeignKey(Admin, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    photo = models.FileField(upload_to='expenses/', null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - ${self.amount} - {self.date.strftime('%Y-%m-%d')}"



class SuperAdmin(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.name



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Expense

@csrf_exempt
def get_all_expenses(request):
    if request.method == 'GET':
        try:
            # Fetch ALL expenses across the company, newest first
            expenses = Expense.objects.all().order_by('-date').select_related('name')
            
            expense_list = []
            for exp in expenses:
                expense_list.append({
                    'id': exp.id,
                    'admin_name': exp.name.name if exp.name else 'Unknown', # Get the Admin's name
                    'amount': float(exp.amount),
                    'date': exp.date.strftime('%Y-%m-%d'),
                    'category': exp.category,
                    'desc': exp.description,
                    'receipt': exp.photo.url if exp.photo else None 
                })
                
            return JsonResponse({'status': 'success', 'data': expense_list})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
