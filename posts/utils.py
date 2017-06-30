from django.template.defaultfilters import slugify
from .models import Tag


# Add tags to the post
def add_tags(post, tag_string="Weekend Trip, Short Trip, Long Trip, Explore Around, Far Away, Look for Passenger, Look for Driver"):
    tags = tag_string.split(",")
    post.tags.set([])
    for tag in tags:
        tag_title = tag.strip()
        tag_slug = slugify(tag_title)
        try:
            tag = Tag.objects.get(slug=tag_slug)
        except:
            tag = Tag.objects.create(title=tag_title)
            
        post.tags.add(tag)

    return post



