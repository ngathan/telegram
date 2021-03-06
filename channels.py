import urllib
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from requests_html import HTMLSession

from common import logger

TELEGAGO_BASE_URL = 'https://cse.google.com/cse?q=+&cx=006368593537057042503:efxu7xprihg#gsc.tab=0&gsc.ref=more%3Apublic&gsc.q='
LYZEM_BASE_URL = 'https://lyzem.com/search?f=channels&l=%3Aen&per-page=100&q='


# extracts the html from a URL using the requests_html library (supports JS)
def extract_html(url, javascript_enabled=False):
    session = HTMLSession()
    response = session.get(url)
    if javascript_enabled:
        response.html.render()
        source_html = response.html.html
        return source_html
    else:
        return response.html.html


# method to parse the HTML from the Lyzem page
def parse_lyzem_page(html):
    soup = BeautifulSoup(html, "lxml")
    links = soup.find_all('li', attrs={'class', 'result'})
    channels = []
    for link in links:
        try:
            element_classes = link['class']
            # if they have this element this means the result is an advertisement
            # we dont want these
            if 'ann' in element_classes:
                continue
            path_url = link['data-url']
            channel_name = path_url.split('?')[0].split('/')[-1]
            if channel_name not in channels:
                channels.append(channel_name)
        except KeyError:
            continue
    return channels


def search_channels_lyzem(query, limit=100):
    initial_request_url = LYZEM_BASE_URL + urllib.parse.quote(query)
    logger.debug("Lyzem request url {}".format(initial_request_url))

    # extract channels from initial page
    source_html = extract_html(initial_request_url, javascript_enabled=False)
    page_channels = parse_lyzem_page(source_html)
    all_channels = page_channels

    # if reached limit return the channels
    if len(all_channels) >= limit:
        return all_channels[:limit]

    # otherwise we need to go to next pages
    # find the number of pages from the html
    soup = BeautifulSoup(source_html, "lxml")
    cursor_div = soup.find_all('nav', {'class': 'pages'})
    try:
        num_pages = len(cursor_div[0].find_all('li'))
    except IndexError:
        num_pages = 0
        pass

    # then iterate over all pages to extract all channels
    for i in range(num_pages):
        request_url = initial_request_url + '&p=' + str(i + 1)
        logger.debug("Lyzem request url {}".format(request_url))
        source_html = extract_html(request_url, javascript_enabled=False)
        page_channels = parse_lyzem_page(source_html)
        for channel in page_channels:
            if channel not in all_channels:
                all_channels.append(channel)
        if len(all_channels) >= limit:
            return all_channels[:limit]
    return all_channels


# method to parse the HTML from the telegago page
def parse_telegago_page(html):
    soup = BeautifulSoup(html, "lxml")
    links = soup.find_all('a', attrs={'class', 'gs-title'})

    channels = []

    for link in links:
        try:
            path_url = urlparse(link['href']).path
            if path_url.startswith('/s/'):
                if path_url.count('/') == 2:
                    channel_name = path_url.split('/')[-1]
                else:
                    channel_name = path_url.split('/')[-2]
            else:
                channel_name = path_url.split('/')[1]
            if channel_name not in channels:
                channels.append(channel_name)
        except KeyError:
            continue
    return channels


def search_channels_telegago(query, limit=100):
    initial_request_url = TELEGAGO_BASE_URL + urllib.parse.quote(query)
    logger.debug("Telegago request url {}".format(initial_request_url))

    # extract channels from initial page
    source_html = extract_html(initial_request_url, javascript_enabled=True)
    page_channels = parse_telegago_page(source_html)
    all_channels = page_channels

    # if reached limit return the channels
    if len(all_channels) >= limit:
        return all_channels[:limit]

    # otherwise we need to go to next pages
    # find the number of pages from the html
    soup = BeautifulSoup(source_html, "lxml")
    cursor_div = soup.find_all('div', {'class': 'gsc-cursor'})
    try:
        num_pages = len(cursor_div[0].find_all('div'))
    except IndexError:
        num_pages = 0
        pass

    # then iterate over all pages to extract all channels
    for i in range(num_pages):
        request_url = initial_request_url + '&gsc.page=' + str(i + 1)
        logger.debug("Telegago request url {}".format(request_url))
        source_html = extract_html(request_url, javascript_enabled=True)
        page_channels = parse_telegago_page(source_html)
        for channel in page_channels:
            if channel not in all_channels:
                all_channels.append(channel)
        if len(all_channels) >= limit:
            return all_channels[:limit]
    return all_channels

