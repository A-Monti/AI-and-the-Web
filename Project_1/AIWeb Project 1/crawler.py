import requests                                 #importing necessary modules
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import QueryParser
import os   #to interact with operating system (functions for directory)


schema = Schema(url=ID(unique=True, stored=True), content=TEXT) #whoosh schema for indexing

class WebCrawler: #defining a web crawler class
    def __init__(self, start_url, index_dir):
        print('hi') #delete
        self.start_url = start_url #Initial values for start and visited URLs
        self.visited_urls = set()
        self.index_dir = index_dir #index directory as a storage for indexed data

        if not os.path.exists(index_dir): #if no index directory...
            print('mkdir')
            os.mkdir(index_dir) #...make index directory

        self.index = create_in(self.index_dir, schema=schema) #creating search index with whoosh schema

    def crawl(self): #crawl method
        queue = [self.start_url] #queue with starting URL
        while queue: #while loop until queue is empty
            url = queue.pop() #get next URL
            if url not in self.visited_urls: #if URL not yet visited
                try:
                    response = requests.get(url) #send GET-request to URL
                    if response.status_code == 200: #if status OK
                        content = response.text #get response content
                        self.index_page(url, content) #indexing page content
                        print('Add to Index: '+str(url)) #delete
                        soup = BeautifulSoup(content, 'html.parser') #parsing URL content with BeautifulSoup library
                        for link in soup.find_all('a'):
                            next_url = link.get('href') #get method for extracting next URL from href attribute
                            if next_url: #if valid URL is extracted
                                next_url = urljoin(url, next_url) #join next URL with current URL (for absolute URL)
                                parsed_url = urlparse(next_url) #parse next URL
                                if parsed_url.netloc == urlparse(self.start_url).netloc: #check is domain same as starting URL (netloc=network location)
                                    queue.append(next_url) #add next URL
                    self.visited_urls.add(url) #URL = visited
                except Exception as e: #if crawling failes
                    print(f"Error crawling {url}: {str(e)}")

    def index_page(self, url, content): #method for indexing a page with specified URL and content
        writer = self.index.writer() #writer for search index
        writer.add_document(url=url, content=content) #add URL and content to index
        writer.commit() #commit changes to index

    def search(self, query): #searching index for specified query
        query_parser = QueryParser("content", schema=schema) #Query parser for content of schema
        with self.index.searcher() as searcher: #open searcher
            query = query_parser.parse(query) #parse query
            results = searcher.search(query, limit=None) #performing search and retrieving results
            return [result['url'] for result in results] #return list of URLs from search results