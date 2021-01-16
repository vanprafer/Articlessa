from django.shortcuts import render
import requests
import bs4
from visualizer.models import Article

def f(request):
    query = request.GET.get('query', '')
    ctx = {
        'articles': scrapping_biorxiv(query)
    }
    return render(request, 'index.html', ctx)

def scrapping_arxiv(query):
    query = query.replace(' ', '+')
    url = 'https://arxiv.org/search/?query={}&searchtype=all&source=header'.format(query)
    html_arxiv = requests.get(url).text
    bs = bs4.BeautifulSoup(html_arxiv, features='html.parser')

    results = bs.select('li.arxiv-result')
    articles = []

    for html_article in results:
        title = html_article.select('p.title')[0].text.strip()
        html_authors = html_article.select('p.authors a')
        authors = ', '.join([a.text.strip() for a in html_authors]) # Separa a los autores por coma
        date = html_article.select('p.is-size-7')[0].text.split(';')[0].replace('Submitted', '').strip()
        #abstract = html_article.select('p.abstract span.abstract')[0].text
        article = Article(title, authors, date, 'abstract')
        articles.append(article)

    return articles

def scrapping_f1000research(query):
    query = query.replace(' ', '+')
    url = 'https://f1000research.com/search?q={}'.format(query)
    html_f1000research = requests.get(url).text
    bs = bs4.BeautifulSoup(html_f1000research, features='html.parser')

    results = bs.select('div.article-browse-wrapper')
    articles = []

    for html_article in results:
        title = html_article.select('span.article-title')[0].text.strip()
        html_authors = html_article.select('span.js-article-author')
        authors = ', '.join([a.text.strip() for a in html_authors]) # Separa a los autores por coma
        date = html_article.select('div.article-bottom-bar')[0].text.split('PUBLISHED')[-1].strip()
        #abstract = html_article.select('p.abstract span.abstract')[0].text
        article = Article(title, authors, date, 'abstract')
        articles.append(article)

    return articles

def scrapping_biorxiv(query):
    query = query.replace(' ', '+')
    url = 'https://www.biorxiv.org/search/{}'.format(query)
    html_biorxiv = requests.get(url).text
    bs = bs4.BeautifulSoup(html_biorxiv, features='html.parser')

    results = bs.select('div.highwire-cite-highwire-article')
    articles = []

    for html_article in results:
        title = html_article.select('span.highwire-cite-title')[0].text.strip()
        authors = html_article.select('span.highwire-citation-authors')[0].text
        date = '/'.join(html_article.select('span.highwire-cite-metadata-pages')[0].text.split('.')[:-1]) # Sacar fecha del doi eliminando el último elemento del punto
        #abstract = html_article.select('p.abstract span.abstract')[0].text
        article = Article(title, authors, date, 'abstract')
        articles.append(article)

    return articles