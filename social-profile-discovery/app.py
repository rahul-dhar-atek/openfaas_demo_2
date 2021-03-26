from flask import Flask, request, jsonify
from waitress import serve
import os

# important libs
import requests, json 
from googleapiclient.discovery import build

import re
import requests
from bs4 import BeautifulSoup as bfs

from urllib.parse import urlparse

app = Flask(__name__)

# All keys
api_key = 'AIzaSyBiw0igjEzad039Ee-gHhEtDpYe7egxIiE'
cse_id = '7ca7d769c2c72e0c9'

def getData(query):
    # all declarations
    all_get_data = list()
    data = list()
    links = list()


    # google search function
    def google_search(search_term, api_key, cse_id, **kwargs):
        service = build("customsearch", "v1", developerKey=api_key)
        web_res = service.cse().list(q=search_term, cx=cse_id,  **kwargs).execute()
        image_res = service.cse().list(q=search_term, cx=cse_id,searchType='image',  **kwargs).execute()
        
        return web_res, image_res 

    web_result, image_result = google_search(query, api_key, cse_id)

    # Get Data from cse Web Search
    try:
        for item in web_result['items']:
            all_get_data.append([item['title'], item['link'], item['snippet']])
    except:
        pass

    # Get data from cse image search
    try:
        for item in image_result['items']:
            all_get_data.append([item['title'], item['image']['contextLink'], item['snippet']])
    except:
        pass
        
        

    for get_data in all_get_data:
        links.append(get_data[1])
        
        string = get_data[2]
        try:
            links.append(re.search("(?P<url>https?://[^\s]+)", string).group("url"))
        except:
            pass
            
    # Fetch Google Search Data
    results = requests.get(f'https://www.google.com/search?q={query}')

    # Scrape fetched data from BeautifulSoup
    soup = bfs(results.text, "lxml") 

    # get all data with <a> tag
    a_tags = soup.find_all('a')

    for tag in a_tags:
        # get all data with <href> or hyperlink
        href_tags = tag.get('href')
        
        try:
            m = re.search("(?P<url>https?://[^\s]+)", href_tags)
            n = m.group(0)
            rul = n.split('&')[0]
            domain = urlparse(rul)
            
            if(re.search('google.com', domain.netloc)):
                continue
            else:
                links.append(rul)
                
        except:
            continue
            

    links = list(set(links))

    for link in links:
        data.append(
        {
            'handle': link,
            'platform': urlparse(link).netloc
        })


    # In[21]:


    return data
    

# distutils.util.strtobool() can throw an exception
def is_true(val):
    return len(val) > 0 and val.lower() == "true" or val == "1"

@app.before_request
def fix_transfer_encoding():
    """
    Sets the "wsgi.input_terminated" environment flag, thus enabling
    Werkzeug to pass chunked requests as streams.  The gunicorn server
    should set this, but it's not yet been implemented.
    """

    transfer_encoding = request.headers.get("Transfer-Encoding", None)
    if transfer_encoding == u"chunked":
        request.environ["wsgi.input_terminated"] = True

@app.route("/", defaults={"path": ""}, methods=["POST", "GET"])
def home(path):
    
    try:
        json_req = request.json
        data = getData(json_req["handle"])

        return json.dumps({"data": data, "error": None})
    
    except Exception as e:
        return json.dumps({"data": None, "error": None})

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)