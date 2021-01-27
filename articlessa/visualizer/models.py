from django.db import models
from whoosh.fields import Schema, TEXT, DATETIME
from whoosh.analysis import StemmingAnalyzer

# Create your models here.

class Article:
    def __init__(self, title, authors, date, url):
        self.title = title
        self.authors = authors
        self.date = date
        self.url = url

Article.schema = Schema(
    title = TEXT(sortable=True, stored=True),
    authors = TEXT(sortable=True, stored=True),
    date = DATETIME(sortable=True, stored=True),
    url = TEXT(stored=True)
)

