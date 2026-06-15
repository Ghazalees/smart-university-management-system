from django.contrib import admin
from .models import Question, QuestionHistory, QuestionResponse
admin.site.register([Question, QuestionHistory, QuestionResponse])
