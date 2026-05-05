from django.db import models

# Create your models here.


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
    experiences=models.CharField(max_length=30 ,default=0)
    passed_out=models.CharField(max_length=4)
    status = models.CharField(
    max_length=30,
    default="form_pending"
)
    fee = models.DecimalField(max_digits=10,null=True,blank=True, decimal_places=2)


    
    def __str__(self):
        return self.name.name
    
# class Call_screening(models.Model):
#     candidate = models.ForeignKey(Candidate_Form, on_delete=models.CASCADE)
#     screening_date = models.DateTimeField()
#     interviewer = models.CharField(max_length=100)
#     def __str__(self):
#         return f"Call Screening for {self.candidate.name} on {self.screening_date}"

class Interview(models.Model):
    name = models.ForeignKey(Candidate_Form, on_delete=models.CASCADE)
    interview_date = models.DateTimeField()
    interviewer = models.CharField(max_length=100)
    link = models.URLField()
    
    
#     def __str__(self):
#         return f"Interview for {self.name.name} on {self.interview_date}"
    
class payment(models.Model):
    candidate = models.ForeignKey(Candidate_Form, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    screenshot = models.FileField(upload_to='screenshots/')
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return f"Payment of {self.amount} for {self.candidate.name} on {self.payment_date}"

# class Offer(models.Model):
#     name = models.ForeignKey(Candidate_Form, on_delete=models.CASCADE)
#     joining_date = models.DateTimeField()
#     position = models.CharField(max_length=100)
#     salary = models.DecimalField(max_digits=10, decimal_places=2)
#     offer_letter = models.FileField(upload_to='offer_letters/') 
    
#     def __str__(self):
#         return f"Offer for {self.name.name} for position {self.position} with salary {self.salary}"
    
class Document(models.Model):
    name = models.ForeignKey(Candidate_Form, on_delete=models.CASCADE)
    aadhar_card = models.FileField(upload_to='documents/')
    pan_card = models.FileField(upload_to='documents/')
    ssc = models.FileField(upload_to='documents/')
    hsc = models.FileField(upload_to='documents/')
    graduation = models.FileField(upload_to='documents/')
    post_graduation = models.FileField(upload_to='documents/')
    photo= models.FileField(upload_to='documents/')
    def __str__(self):
        return f"Documents for {self.name.name}"