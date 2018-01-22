from django.core.exceptions import ObjectDoesNotExist

from communicator.forms import URLForm
from communicator.models import Corpus, Ignored
from selenium import webdriver

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import re
import time
import celery
from bs4 import BeautifulSoup
from collections import Counter

class Scrape(celery.Task):

    def scrape_rating(self, url, rating):
        url += '/review?setDevice=desktop&rating=' + str(rating)

        self.driver.get(url)

        data = []
        r = re.compile(r'\W+')

        page = 1
        while True:
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            for p in soup.find_all(attrs={'class': re.compile(r'review-body')}):
                data += r.split(p.text.lower())

            try:
                next_button = self.driver.find_element_by_class_name("icon-chevron-right")
                next_button.click()
                time.sleep(5)
                page += 1
            except NoSuchElementException:
                break
            except:
                print("uncaught exception, will break, page : " + str(page))
                break

        return Counter(data)

    def fit_corpus(self, word, occurence, rating):
        if Ignored.objects.filter(word=word).exists():
            return

        try:
            corpus = Corpus.objects.get(rating=rating, word=word)
            corpus.occurence += occurence
        except ObjectDoesNotExist:
            corpus = Corpus(rating=rating, word=word, occurence=occurence)

        corpus.save()

    def crawl(self, url):
        for rating in range(1, 6):
            data = self.scrape_rating(url, rating)
            for word, occurence in data.items():
                self.fit_corpus(word, occurence, rating)

    def scrape(self, content, **kwargs):
        form = URLForm(content)

        if form.is_valid():
            options = webdriver.ChromeOptions()
            # options.add_argument('headless')
            # options.add_argument('window-size=1280x720')
            self.driver = webdriver.Chrome(chrome_options=options)
            self.crawl(form.cleaned_data['url'])
            self.driver.close()
            return {'status': 'success'}
        else:
            return form.errors

@celery.shared_task(base=Scrape)
def scrape(content, **kwargs):
    scraper = Scrape()
    scraper.scrape(content, **kwargs)
