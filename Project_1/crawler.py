# Define the skeleton of the crawling along the algorithm

## whoosh/ flask    py

def crawler_alg(original_url):
    crawler = [original_url]
    visited = []

    # While Stack is not empty
    while crawler:
        # Pop first URL
        url = crawler.pop()

        # If not visited recently
        if url not in visited:
            # Get Content
            print("hello!")

            # Analyse, update index, find links to other websites
            # Push URL to Stack
            # crawler.append(new_url)
            # Update visited List
            visited.append(url)

# index = {keyword: URL}
index = {}

def search(list_words):
    links = []
    for word in list_words:
        if word in index:
            links.append(index[word])


crawler_alg("https://vm009.rz.uos.de/crawl/index.html")