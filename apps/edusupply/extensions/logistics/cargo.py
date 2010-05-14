#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models

class CargoWithCondition(models.Model):
    CONDITION_CHOICES = (
        ('G', 'Good'),
        ('D', 'Damaged'),
        ('L', 'Alternate delivery location'),
    )
    condition = models.CharField(max_length=3, choices=CONDITION_CHOICES)
    
    class Meta:
        abstract = True
