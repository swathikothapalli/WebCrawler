import csv
import ssl
import threading
from urllib.error import URLError
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from bs4.element import Comment
import re
from datetime import datetime
import tldextract
from urllib.request import Request, urlopen
import main


class Crawler(threading.Thread):
    def __init__(self, base_url, url_queue, visited, error_links, url_lock, thread_num):
        threading.Thread.__init__(self)
        print(f"Web Crawler worker {threading.current_thread()} has Started")
        self.base_url = base_url
        self.links_queue = url_queue
        self.visited = visited
        self.error_links = error_links
        self.url_lock = url_lock
        self.threadNo = thread_num

    def tag_visible(self, element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        if re.match(r"[\n]+", str(element)): return False
        return True

    def run(self):
        global lck
        global pagecount
        my_ssl = ssl.create_default_context()
        my_ssl.check_hostname = False
        my_ssl.verify_mode = ssl.CERT_NONE

        while True:
            now = datetime.now()
            timestamp = datetime.timestamp(now)
            link = self.links_queue.get()
            link = urljoin(self.base_url, link)
            domain = tldextract.extract(link).domain
            if domain in main.conf['blacklist']:
                continue

            domain_visited = self.visited.get(domain, 0)
            if domain_visited == 0:
                domain_visited = []

            if link is None:
                break

            if len(domain_visited) != 0:
                find = [item for item in domain_visited if link in item]
                if len(find) > 0:
                    find = tuple(find)
                    if (now - find[0][1]).total_seconds() < 86400:
                        continue
                    else:
                        self.visited[domain].remove(find[0])

            try:
                req = Request(link, headers={'User-Agent': 'Mozilla/5.0'})
                try:
                    response = urlopen(req, context=my_ssl)
                except:
                    continue

                soup = BeautifulSoup(response.read(), "html.parser")
                text = soup.prettify()

                texts = soup.findAll(text=True)

                visible_texts = filter(self.tag_visible, texts)
                text = u",".join(t.strip() for t in visible_texts)
                text = text.lstrip().rstrip()
                text = text.split(',')
                post_text = ''
                for sen in text:
                    if sen:
                        if len(sen.split(' ')) > 5:
                            sen = sen.rstrip().lstrip()
                            post_text += sen + ' '
                if len(post_text.split(' ')) < 6:
                    continue
                lck.acquire()
                crawler_file = open(main.crawled_csv, mode='a')
                crawler_writer = csv.writer(crawler_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL,
                                            escapechar='\\')
                crawler_writer.writerow([timestamp, hash, link, post_text, "No", "N/A", " "])
                pagecount = pagecount + 1
                crawler_file.close()
                lck.release()

                if type(soup.find_all('a')) == 'NoneType':
                    print("No links found in this page!")
                    continue
                else:
                    for a_tag in soup.find_all('a'):
                        links = a_tag.get("href")
                        if len(domain_visited) == 0:
                            self.links_queue.put(links, 1)
                        else:
                            if (links not in domain_visited):
                                self.links_queue.put(links, 1)

                if len(domain_visited) != 0:
                    self.visited[domain].append((link, now))
                else:
                    self.visited[domain] = [(link, now)]
            except URLError as e:
                self.error_links.append(link)
            finally:
                self.links_queue.task_done()
