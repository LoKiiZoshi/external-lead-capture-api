from rest_framework import serializers
from .models import Review, ItemReview, ReviewAnalytics
import re
from textblob import TextBlob  # For basic sentiment analysis
from decimal import Decimal


class ItemReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for ItemReview model
    """
    
    class Meta:
        model = ItemReview
        fields = [
            'id', 'menu_item_id', 'rating', 'comment', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating reviews with nested item reviews
    """
    item_reviews = ItemReviewSerializer(many=True, required=False)
    
    class Meta:
        model = Review
        fields = [
            'order_id', 'session_id', 'restaurant_id', 
            'overall_rating', 'food_rating', 'service_rating', 'ambiance_rating',
            'comment', 'is_anonymous', 'item_reviews'
        ]
    
    def validate_overall_rating(self, value):
        """Validate overall rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Overall rating must be between 1 and 5")
        return value
    
    def validate_food_rating(self, value):
        """Validate food rating if provided"""
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("Food rating must be between 1 and 5")
        return value
    
    def validate_service_rating(self, value):
        """Validate service rating if provided"""
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("Service rating must be between 1 and 5")
        return value
    
    def validate_ambiance_rating(self, value):
        """Validate ambiance rating if provided"""
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("Ambiance rating must be between 1 and 5")
        return value
    
    def analyze_sentiment(self, text):
        """
        Simple AI sentiment analysis using TextBlob
        Returns sentiment score between -1 and 1
        """
        if not text or not text.strip():
            return None
        
        try:
            # Clean the text
            cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
            
            # Use TextBlob for sentiment analysis
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            # Ensure the score is within bounds
            return max(-1.0, min(1.0, polarity))
        except Exception:
            return None
    
    def create(self, validated_data):
        """
        Create review with nested item reviews and sentiment analysis
        """
        item_reviews_data = validated_data.pop('item_reviews', [])
        
        # Analyze sentiment if comment is provided
        comment = validated_data.get('comment')
        if comment:
            sentiment_score = self.analyze_sentiment(comment)
            validated_data['sentiment_score'] = sentiment_score
        
        # Create the main review
        review = Review.objects.create(**validated_data)
        
        # Create item reviews
        for item_review_data in item_reviews_data:
            ItemReview.objects.create(review=review, **item_review_data)
        
        return review


class ReviewListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing reviews with read-only fields
    """
    item_reviews = ItemReviewSerializer(many=True, read_only=True)
    sentiment_label = serializers.CharField(source='get_sentiment_label', read_only=True)
    average_specific_rating = serializers.DecimalField(
        max_digits=3, decimal_places=2, read_only=True
    )
    
    class Meta:
        model = Review
        fields = [
            'id', 'order_id', 'session_id', 'restaurant_id',
            'overall_rating', 'food_rating', 'service_rating', 'ambiance_rating',
            'comment', 'is_anonymous', 'sentiment_score', 'sentiment_label',
            'average_specific_rating', 'item_reviews',
            'created_at', 'updated_at'
        ]


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing reviews (limited fields)
    """
    
    class Meta:
        model = Review
        fields = [
            'overall_rating', 'food_rating', 'service_rating', 'ambiance_rating',
            'comment', 'is_anonymous'
        ]
    
    def validate_overall_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Overall rating must be between 1 and 5")
        return value
    
    def update(self, instance, validated_data):
        """
        Update review and re-analyze sentiment if comment changed
        """
        comment = validated_data.get('comment')
        
        # Re-analyze sentiment if comment is being updated
        if comment and comment != instance.comment:
            sentiment_score = self.analyze_sentiment(comment)
            validated_data['sentiment_score'] = sentiment_score
        
        return super().update(instance, validated_data)


class ReviewAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for review analytics
    """
    sentiment_distribution = serializers.SerializerMethodField()
    
    class Meta:
        model = ReviewAnalytics
        fields = [
            'restaurant_id', 'total_reviews',
            'average_overall_rating', 'average_food_rating',
            'average_service_rating', 'average_ambiance_rating',
            'sentiment_distribution', 'last_updated'
        ]
    
    def get_sentiment_distribution(self, obj):
        """
        Return sentiment distribution as percentages
        """
        total = obj.total_reviews
        if total == 0:
            return {
                'positive': 0,
                'neutral': 0,
                'negative': 0
            }
        
        return {
            'positive': round((obj.positive_sentiment_count / total) * 100, 1),
            'neutral': round((obj.neutral_sentiment_count / total) * 100, 1),
            'negative': round((obj.negative_sentiment_count / total) * 100, 1)
        }


class RestaurantReviewSummarySerializer(serializers.Serializer):
    """
    Serializer for restaurant review summary with filters
    """
    restaurant_id = serializers.UUIDField()
    total_reviews = serializers.IntegerField()
    average_overall_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    rating_distribution = serializers.DictField()
    recent_reviews = ReviewListSerializer(many=True)
    top_rated_items = serializers.ListField()
    sentiment_summary = serializers.DictField()


class ReviewFilterSerializer(serializers.Serializer):
    """
    Serializer for review filtering parameters
    """
    restaurant_id = serializers.UUIDField(required=False)
    min_rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    max_rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    sentiment = serializers.ChoiceField(
        choices=['positive', 'neutral', 'negative'], 
        required=False
    )
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    is_anonymous = serializers.BooleanField(required=False)
    has_comment = serializers.BooleanField(required=False)