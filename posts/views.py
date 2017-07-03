from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveAPIView
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.views import APIView
import ast
# from rest_framework import status
# from rest_framework.views import APIView
# from rest_framework.response import Response

from .models import Post, Tag, Category, Settings
from .serializers import CreatePostSerializer, PostSerializer, TagSerializer, CategorySerializer, SettingsSerializer
from .utils import add_tags
from .activities import submit_post

class SmallResultsSetPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = 'page_size'
    max_page_size = 1


# class PostList(ListAPIView):
#     queryset = Post.objects.all()
#     serializer_class = PostSerializer
#     pagination_class = SmallResultsSetPagination

#     def get_queryset(self):
#         qs = super(PostList, self).get_queryset()

#         # Filter by tag
#         tag = self.kwargs.get('tag')
#         if tag:
#             tag = Tag.objects.get(slug=tag)
#             return qs.filter(tags=tag)

#         # Filter by category
#         category = self.kwargs.get('category')
#         if category:
#             category = Category.objects.get(slug=category)
#             return qs.filter(category=category)
        # return qs
    
class PostList(APIView):
    pagination_class = SmallResultsSetPagination
    def get(self, request, format=None):
        #assuming every other field in the model has a default value    

        #for a clear example
        post_list = Post.objects.all()

        page = self.paginate_queryset(post_list)
        if page is not None:
            serializer = PostSerializer(page, many=True)
        else:
            serializer = PostSerializer(post_list, many=True)
        serializer_data = serializer.data
        for index, data in enumerate(serializer_data):
            data = dict(data)
            if data['outside_trip_details']:
                data['outside_trip_details'] = ast.literal_eval(data['outside_trip_details'])
            if data['full_trip_details']:
                data['full_trip_details'] = ast.literal_eval(data['full_trip_details'])
            serializer_data[index] = data
        return self.get_paginated_response(serializer_data)

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)


@permission_classes((IsAuthenticated, ))    
class PostCreate(CreateAPIView):
    queryset = Post.objects.all()    
    serializer_class = CreatePostSerializer
    
    def perform_create(self, serializer):
        post = serializer.save()

        # Set category
        try:
            category = str(self.request.data['category'])
        except:
            category = ""        
        if category:
            category = Category.objects.get(slug=category)
            post.category = category
        
        # Add tags
        try:
            tag_string = self.request.data['tags']
        except:
            tag_string = ""
        if tag_string:
            post = add_tags(post, tag_string)

        post.save()

        # Ignore this.
        # Experimenting with submitting posts using ActivityPub.
        try:
            submit_post(post)
        except:
            pass

# @permission_classes((IsAuthenticated, ))
# @permission_classes((AllowAny, ))
class PostRetrieveUpdateDestroy(RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = 'slug'

        
    def perform_update(self, serializer):
        post = serializer.save()

        # Set category
        try:
            category = str(self.request.data['category'])
        except:
            category = ""        
        if category:
            category = Category.objects.get(slug=category)
            post.category = category

        # Replace tags
        try:
            tags = str(self.request.data['tags'])
        except:
            tags = ""        
        if tags:
            post = add_tags(post, tags)

        post.save()
    

class TagListCreate(ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class TagRetrieveUpdateDestroy(RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'slug'    

class CategoryList(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class SettingsDetail(RetrieveAPIView):
    serializer_class = SettingsSerializer

    def get_object(self):
        queryset = Settings.objects.all().first()
        return queryset