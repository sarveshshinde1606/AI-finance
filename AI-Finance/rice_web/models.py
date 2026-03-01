from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField()

    def __str__(self):
        return self.user.username

class UserProgress(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    topic = models.CharField(max_length=200)
    panel_type = models.CharField(max_length=50)  # quiz / game
    score = models.IntegerField()
    total_questions = models.IntegerField()
    xp_earned = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.topic} ({self.score}/{self.total_questions})"

from django.db import models
from django.contrib.auth.models import User

class HumanAssistantRequest(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    admin_remark = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject



class BudgetPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    salary = models.FloatField()
    rent = models.FloatField()
    food = models.FloatField()
    transport = models.FloatField()
    savings_percent = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def total_expenses(self):
        return self.rent + self.food + self.transport

    def savings_amount(self):
        return (self.salary * self.savings_percent) / 100

    def remaining_balance(self):
        return self.salary - self.total_expenses() - self.savings_amount()

    