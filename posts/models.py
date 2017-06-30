# -*- coding: utf-8 -*-
import datetime
import uuid # for unique slug
from django.db import models
from django.template.defaultfilters import slugify
from django.conf import settings
from django.db.models import permalink

# Generate unique slug
def unique_slug(title):
    uniqueid = uuid.uuid1().hex[:5]                
    slug = slugify(title) + "-" + str(uniqueid)

    if not Post.objects.filter(slug=slug).exists():
        # If there's no posts with such slug,
        # then the slug is unique, so I return it
        return slug
    else:
        # If the post with this slug already exists -
        # I try to generate unique slug again
        return unique_slug(title)

    
class Post(models.Model):
    #future: add custom trip!
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=256, default="")
    pub_date = models.DateTimeField(blank=True, null=True)
    body = models.TextField(default="", null=True, blank=True)
    published = models.BooleanField(default=False, blank=True)
    visible = models.BooleanField(default=True, blank=True)
    full_trip = models.ForeignKey('travel_with_friends.FullTripTable',
                                  related_name="posts",
                                  blank=True, null=True)  
    outside_trip = models.ForeignKey('travel_with_friends.OutsideTripTable',
                                  related_name="posts",
                                  blank=True, null=True)  
    category = models.ForeignKey('Category',
                                  related_name="posts",
                                  blank=True, null=True)    

    tags = models.ManyToManyField('Tag',
                                  related_name="posts",
                                  blank=True)

    score = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title

    def save(self, slug="", *args, **kwargs):
        if not self.id:
            self.pub_date = datetime.datetime.now()
            self.slug = unique_slug(self.title)

        return super(Post, self).save(*args, **kwargs)

    @permalink
    def get_absolute_url(self):
        return ('post_detail', None, {'slug': self.slug })

    
    class Meta:
        ordering = ('-pub_date',)

class Tag(models.Model):
    title = models.CharField(max_length=64)    
    slug = models.SlugField(max_length=64, default="")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.title)
        super(Tag, self).save(*args, **kwargs)

        
    @permalink
    def get_absolute_url(self):
        return ('view_tag', None, {'slug': self.slug })

class Category(models.Model):
    title = models.CharField(max_length=64)    
    slug = models.SlugField(max_length=64, default="")
    description = models.TextField(max_length=512, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Category, self).save(*args, **kwargs)

        
    @permalink
    def get_absolute_url(self):
        return ('view_category', None, {'slug': self.slug })

    class Meta:
        verbose_name_plural = "categories"