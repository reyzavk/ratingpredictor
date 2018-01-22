from djongo import models

# Create your models here.

class Corpus(models.Model):
    rating = models.IntegerField()
    word = models.CharField(max_length=100)
    occurence = models.IntegerField()
    objects = models.DjongoManager()

    def __str__(self):
        return str(self.rating) + ' star : ' + self.word

class Ignored(models.Model):
    word = models.CharField(max_length=100)
    description = models.CharField(max_length=100, null=True, blank=True)
    objects = models.DjongoManager()

    def __str__(self):
        return self.word
