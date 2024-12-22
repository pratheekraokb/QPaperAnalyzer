from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

import re
class QPaperModule:
    def topicsFromSyllabus(syllabus):
        topics = re.split(r'(?<=\.)\s*–', syllabus.replace('\n', ' '))
        cleaned_topics = []
        for topic in topics:
            sub_topics = re.split(r'\.\s+', topic) 
            for sub_topic in sub_topics:
                if sub_topic.strip():
                    cleaned_topics.append(sub_topic.strip().rstrip('.'))
        return cleaned_topics


def index(request):
    return render(request, 'students/index.html')
