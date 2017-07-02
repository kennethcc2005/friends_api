from rest_framework import serializers
from .models import Post, Tag, Category, Settings

class TagSlugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'title',
            'slug',
        )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            'title',
            'slug',
        )
        

class PostSerializer(serializers.ModelSerializer):
    tags = TagSlugSerializer(read_only=True, many=True)
    category = CategorySerializer(read_only=True)
    username = serializers.CharField(source='username.username')
    full_trip_details = serializers.CharField(source='full_trip.details')
    full_trip_id = serializers.CharField(source='full_trip.full_trip_id')
    outside_trip_details = serializers.CharField(source='outside_trip.outside_trip_details')
    outside_trip_id = serializers.CharField(source='outside_trip.outside_trip_id')
    # full_trip_details = ast.literal_eval(full_trip_details)
    class Meta:
        model = Post
        fields = ('username','title', 'slug','body','full_trip_id', 'full_trip_details','outside_trip_id', 'outside_trip_details','published', 'category', 'tags','pub_date')
        lookup_field = 'slug'

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'title',
            'slug',
        )

class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = '__all__'  

