from django.db import models

# Create your models here.

class Menu(models.Model):
    name = models.CharField(max_length=32)

class Group(models.Model):
    title = models.CharField(max_length=32)
    mu = models.ForeignKey(to="Menu",default=1)

class UserInfo(models.Model):
    name = models.CharField(max_length=32)
    pwd = models.CharField(max_length=32)

    group = models.ForeignKey(to='Group')
    roles = models.ManyToManyField(to='Role')


class Role(models.Model):
    name = models.CharField(max_length=32)