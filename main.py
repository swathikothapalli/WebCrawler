# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

# Press the green button in the gutter to run the script.
import csv
import os
import time
import threading
import re
from datetime import datetime
from matplotlib import pyplot as plt
from transformers import AutoTokenizer, AutoModel
import warnings
import priorityQueue
import myCrawler
import Classifier


def count_pages_donwloaded():
    global speed_ctr
    threading.Timer(10, count_pages_donwloaded).start()
    speed_samples.append(pagecount)
    speed_ctr = speed_ctr + 1

    print(f"{pagecount} web pages got downloaded")

    if speed_ctr > 30:
        speed_ctr = 0
        plt.plot(speed_samples)
        plt.show()

    for i, thread in enumerate(c_threads):
        if thread.is_alive() == False and thread.name == "crawler":
            crawler = myCrawler.Crawler(base_url=thread.base_url,
                                        url_queue=thread.links_queue,
                                        visited=thread.visited,
                                        error_links=thread.error_links,
                                        url_lock=thread.url_lock,
                                        thread_num=thread.threadNo)
            del c_threads[i]
            crawler.start()
            c_threads.append(crawler)

            crawler.join()
        elif thread.is_alive() == False and thread.name == "classifer":
            classifier = Classifier.Classifier()
            classifier.name = "classifer"
            del c_threads[i]
            classifier.start()
            c_threads.append(classifier)

warnings.filterwarnings('ignore')


conf = dict(
    dir='crawler/Spider/',
    base_url=['https://www.worldhistory.org',
              'https://www.newworldencyclopedia.org/',
              'https://www.ushistory.org',
              'https://www.historic-uk.com/',
              'https://hbr.org/',
              'https://newpol.org/',
              'https://pc.net/',
              'https://www.computerhope.com/',
              'https://www.computerlanguage.com/'],
    no_of_threads=9,
    labels=['technology', 'business', 'politics', 'history'],
    blacklist=['facebook', 'instagram', 'youtube']
)

starttime = int(time.time())
crawled_csv = conf['dir'] + 'crawler_' + "{}.csv".format(starttime)
speed_ctr = 0
pagecount = 0
speed_samples = []

lck = threading.Lock()
if os.path.exists(conf['dir']) is False:
    print("Create Directory")
    os.makedirs(conf['dir'])

crawler_file = open(crawled_csv, mode='a')
crawler_writer = csv.writer(crawler_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
crawler_writer.writerow(["timestamp", "hash", "link", "post_text", "processed", "label", "true_label"])
pagecount = pagecount + 1
crawler_file.close()

regular_express = re.compile(r"https?://(\.)?")
base_url = conf["base_url"]
no_of_threads = conf["no_of_threads"]

url_lock = threading.Lock()

visited = []
c_threads = []
error_links = []

count_pages_donwloaded()
before_starting = datetime.now()
links_crawl = []

tokenizer = AutoTokenizer.from_pretrained('deepset/sentence_bert')
model = AutoModel.from_pretrained('deepset/sentence_bert')

for i in range(int(no_of_threads)):
    print(f'Thread no: {i} base_url: {base_url[i]}')
    links_crawl.append(priorityQueue.MyPriorityQueue())
    links_crawl[i].put(base_url[i], 1)
    visited.append({})
    error_links.append([])
    crawler = myCrawler.Crawler(base_url=base_url[i],
                                 url_queue=links_crawl[i],
                                 visited=visited[i],
                                 error_links=error_links[i],
                                 url_lock=url_lock,
                                 thread_num=i)
    crawler.name = "crawler"
    classifier = Classifier.Classifier()

    crawler.start()
    classifier.name = "classifer"
    classifier.start()
    c_threads.append(crawler)
    c_threads.append(classifier)
for crawler in c_threads:
    crawler.join()
