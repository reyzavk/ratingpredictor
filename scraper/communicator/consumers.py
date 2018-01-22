from channels.generic.websockets import JsonWebsocketConsumer

from django.core.exceptions import ObjectDoesNotExist

import re
import time
from collections import Counter

from communicator.tasks import scrape
from communicator.forms import URLForm, WordForm, SentenceForm, ActionForm
from communicator.models import Corpus, Ignored

class NaiveBayes:

    def prior(self, rating):
        print('prior {} : {}'.format(rating, Corpus.objects.filter(rating=rating).count()))
        return Corpus.objects.filter(rating=rating).count()

    def likelihood(self, words, rating):
        match = {'$match': {'rating': rating}}
        group = {'$group': {'_id': None, 'sum': {'$sum': '$occurence'}}}
        project = {'$project': {'_id': 0, 'sum': 1}}
        pipe = [match, group, project]
        aggregator = Corpus.objects.mongo_aggregate(pipeline=pipe)

        try:
            item = next(aggregator)
            pr = item['sum']
        except StopIteration:
            return 0

        pw = 1
        multiplier = 0
        for word, occurence in words.items():
            try:
                corpus = Corpus.objects.get(word=word, rating=rating)
            except ObjectDoesNotExist:
                multiplier += 1.1
                continue

            multiplier += occurence

            if corpus.occurence == 1:
                pw *= 1.5 ** occurence
            else:
                pw *= corpus.occurence ** occurence

        print('likelihood {} : {} / {}'.format(rating, pw, (pr ** multiplier)))
        return pw / (pr ** multiplier)

    def posterior(self, words, rating):
        return self.prior(rating) * self.likelihood(words, rating)

    def predict(self, content, *kwargs):
        form = SentenceForm(content)
        if form.is_valid():
            sentence = form.cleaned_data['sentence']

            r = re.compile(r'\W+')
            sentence = r.split(sentence.lower())
            words = Counter(sentence)

            idx, val = max(enumerate(self.posterior(words, rating) for rating in range(1, 6)), key=lambda x: x[1])
            return {'prediction': idx + 1}
        else:
            return form.errors

class Ignorant:

    def unignore(self, content, **kwargs):
        form = WordForm(content)
        if form.is_valid():
            word = form.cleaned_data['word']
            ignored = Ignored.objects.filter(word=word)

            if ignored.exists():
                ignored.delete()

            status = {'status': 'success'}
            return status
        else:
            return form.errors

    def ignore(self, content, **kwargs):
        form = WordForm(content)
        if form.is_valid():
            form.save()
            word = form.cleaned_data['word']
            corpus = Corpus.objects.filter(word=word)
            if corpus.exists():
                corpus.delete()

            status = {'status': 'success'}
            return status
        else:
            return form.errors

class Query:

    def ignored(self, content, **kwargs):
        ignored = Ignored.objects.all()
        ignored = [i.word for i in ignored]
        return {'words': ignored}

    def word(self, content, **kwargs):
        words = Corpus.objects.all()
        words = [w.word for w in words]
        return {'words': words}

class CommunicationBridge:

    ignorant = Ignorant()
    naive_bayes = NaiveBayes()
    query = Query()

    def scrape(self, content, **kwargs):
        scrape.delay(content, **kwargs)

    def get_ignored(self, content, **kwargs):
        return self.query.ignored(content, **kwargs)

    def get_word(self, content, **kwargs):
        return self.query.word(content, **kwargs)

    def ignore(self, content, **kwargs):
        return self.ignorant.ignore(content, **kwargs)

    def unignore(self, content, **kwargs):
        return self.ignorant.unignore(content, **kwargs)

    def predict(self, sentence):
        return self.naive_bayes.predict(sentence)

class CommunicatorConsumer(JsonWebsocketConsumer):

    action = CommunicationBridge()

    def receive(self, content, **kwargs):
        form = ActionForm(content)
        if form.is_valid():
            action = form.cleaned_data['action']
            if action == 'scrape':
                status = self.action.scrape(content, **kwargs)
            elif action == 'ignore':
                status = self.action.ignore(content, **kwargs)
            elif action == 'unignore':
                status = self.action.unignore(content, **kwargs)
            elif action == 'query ignore':
                status = self.action.get_ignored(content, **kwargs)
            elif action == 'query word':
                status = self.action.get_word(content, **kwargs)
            else:
                status = self.action.predict(content, **kwargs)

            if status is not None:
                self.send({'action': action, **status})
        else:
            self.send(form.errors)
