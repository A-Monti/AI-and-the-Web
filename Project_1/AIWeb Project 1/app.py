from flask import Flask, render_template, request, redirect, url_for #import modules from flask for web apps
from crawler import WebCrawler #import web crawler class

app = Flask(__name__) #flask webapp instance

start_url = "https://vm009.rz.uos.de/crawl/index.html" #start URL
index_dir = "search_index" #directory for search index
crawler = WebCrawler(start_url, index_dir) #webcrawler class instance with start URL & index directory

@app.route('/', methods=['GET']) #decorator method
def home():
    return render_template('search_form.html') #rendering search form

@app.route('/search', methods=['GET']) #decorator method for search queries
def search(): #method for getting search query
    query = request.args.get('q') #get search query from query parameters of request
    if query:
        results = crawler.search(query) #perform search using the web crawler

        return render_template('search_results.html', query=query, results=results) #render search results template with query and results
    else:
        return render_template('no_result_found.html', query=query) #if no query provided - back to homepage

if __name__ == '__main__': #run webapp (if executed)
    crawler.crawl() #run crawler
    app.run (debug=True) #run flask app in debug mode