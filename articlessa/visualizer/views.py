from django.shortcuts import render
import requests
import bs4
from visualizer.models import Article
import os
from whoosh import index
from whoosh.qparser import QueryParser
from whoosh.qparser.dateparse import DateParserPlugin
from datetime import datetime
from whoosh.matching.mcore import Matcher
from math import ceil


def articles(request):
    create_index() #GET es un mapa y un atributo no estático de request
    query = request.GET.get('query', '') # No es una request. Se consultan los datos del GET para ver si está la query, si no tuviese datos, devuelve un string vacío
    articles = []
    if query != '':
        articles = scrapping_arxiv(1, query) + scrapping_f1000research(0, query) + scrapping_biorxiv(0, query)
    ctx = {
        'page': 1,
        'next_page': 2,
        'previous_page': 0,
        'max_page': ceil(len(articles) / 10.0),
        'articles': articles[:10],
        'show_filters': articles != [],
        'query': query
    }
    populate_index(articles)
    return render(request, 'articles.html', ctx)

def filters(request):
    query = request.GET.get('query', '')
    title = request.GET.get('title', '')
    authors = request.GET.get('authors', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    page = int(request.GET.get('page', '1'))
    total, articles = search_articles_index(title, authors, date_from, date_to, page)

    ctx = {
        'page': page,
        'next_page': page + 1,
        'previous_page': page - 1,
        'max_page': ceil(total / 10.0),
        'title': title,
        'authors': authors,
        'date_from': date_from,
        'date_to': date_to,
        'articles': articles,
        'query': query,
        'show_filters': True
    }
    return render(request, 'articles.html', ctx)

def scrapping_arxiv(num_pages, query):
    articles = []
    for i in range(num_pages):
        articles += scrapping_arxiv_page(query, i)
    return articles

def scrapping_arxiv_page(query, page):
    query = query.replace(' ', '+')
    url = 'https://arxiv.org/search/?query={}&searchtype=all&source=header&start={}&size=100'.format(query, page * 50)
    html_arxiv = requests.get(url).text
    bs = bs4.BeautifulSoup(html_arxiv, features='html.parser')

    results = bs.select('li.arxiv-result')
    articles = []
    
    for html_article in results:
        title = html_article.select('p.title')[0].text.strip()
        html_authors = html_article.select('p.authors a')
        authors = ', '.join([a.text.strip() for a in html_authors]) # Separa a los autores por coma
        date = html_article.select('p.is-size-7')[0].text.split(';')[0].replace('Submitted', '').strip()
        date_parse = datetime.strptime(date, '%d %B, %Y')
        url = 'https://arxiv.org/pdf/' + html_article.select('a')[0].text[6:].strip()
        article = Article(title, authors, date_parse, url)
        articles.append(article)

    return articles

def scrapping_f1000research(num_pages, query):
    articles = []
    for i in range(num_pages):
        articles += scrapping_f1000research_page(query, i+1)
    return articles

def scrapping_f1000research_page(query, page):
    query = query.replace(' ', '+')
    url = 'https://f1000research.com/search?q={}&show=100&page={}'.format(query, page)
    html_f1000research = requests.get(url).text
    bs = bs4.BeautifulSoup(html_f1000research, features='html.parser')

    results = bs.select('div.article-browse-wrapper')
    articles = []

    for html_article in results:
        title = html_article.select('span.article-title')[0].text.strip()
        html_authors = html_article.select('span.js-article-author')
        authors = ', '.join([a.text.strip() for a in html_authors]) # Separa a los autores por coma
        date = html_article.select('div.article-bottom-bar')[0].text.split('PUBLISHED')[-1].strip()
        date_parse = datetime.strptime(date, '%d %b %Y')
        url = html_article.select('a.article-link')[0]['href'].strip() + '/v1/pdf/'
        article = Article(title, authors, date_parse, url)
        articles.append(article)

    return articles

def scrapping_biorxiv(num_pages, query):
    articles = []
    for i in range(num_pages):
        articles += scrapping_biorxiv_page(query, i)
    return articles

def scrapping_biorxiv_page(query, page):
    query = query.replace(' ', '+')
    url = 'https://www.biorxiv.org/search/{} numresults%3A75?page={}'.format(query, page)
    html_biorxiv = requests.get(url).text
    bs = bs4.BeautifulSoup(html_biorxiv, features='html.parser')

    results = bs.select('div.highwire-cite-highwire-article')
    articles = []

    for html_article in results:
        date = '/'.join(html_article.select('span.highwire-cite-metadata-pages')[0].text.split('.')[:-1]) # Sacar fecha del doi eliminando el último elemento del punto

        if date != '':
            title = html_article.select('span.highwire-cite-title')[0].text.strip()
            authors = html_article.select('span.highwire-citation-authors')[0].text
            url = 'https://www.biorxiv.org' + html_article.select('a.highwire-cite-linked-title')[0]['href'].strip() + '.full.pdf'
                      
            date_parse = datetime.strptime(date, '%Y/%m/%d')
            article = Article(title, authors, date_parse, url)
            articles.append(article)

    return articles

def create_index():
    if not os.path.exists("my_index"):
        os.mkdir("my_index")

    Article.my_index = index.create_in("my_index", Article.schema) # Uso el esquema para crear el índice

def populate_index(articles):
    writer = Article.my_index.writer()

    for article in articles:
        writer.add_document(
            title = article.title,
            authors = article.authors,
            date = article.date,
            url = article.url
        )

    writer.commit()

def search_articles_index(title, authors, date_from, date_to, page):
    parser = QueryParser("title", schema=Article.schema) #creo el parser (esta línea no hace nada más)
                                                         #title es el campo por defecto de búsqueda
                                                         #si se le especifica el artibuto de búsqueda, se va al esquema a buscarlo y valida si existe
    #parser.add_plugin(DateParserPlugin())

    query_list = []

    if title != '':
        subquery_title = 'title:"{}"'.format(title)
        query_list.append(subquery_title)

    if authors != '':
        subquery_authors = 'authors:"{}"'.format(authors)
        query_list.append(subquery_authors)

    if date_from != '' or date_to != '':
        if date_from == '':
            subquery_date = 'date:[TO {}]'.format(date_to)

        elif date_to == '':
            subquery_date = 'date:[{} TO]'.format(date_from)

        else:
            subquery_date = 'date:[{} TO {}]'.format(date_from, date_to)

        query_list.append(subquery_date)


    query = ' AND '.join(query_list)
    parsed_query = parser.parse(query)

    res = []
    total = 0

    with Article.my_index.searcher() as searcher:
        if query == '':
            articles_index = list(searcher.documents())
            search_results = articles_index[(page-1)*10:page*10]
            total = len(articles_index)
        else:
            search_results = searcher.search_page(parsed_query, page)
            total = len(search_results)
            
        for i in search_results:
            res.append(dict(i))

    return total, res
    