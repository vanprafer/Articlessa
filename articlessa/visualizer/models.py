from django.db import models

# Create your models here.

class Article:
    def __init__(self, title, authors, date, abstract):
        self.title = title
        self.authors = authors
        self.date = date
        self.abstract = abstract

