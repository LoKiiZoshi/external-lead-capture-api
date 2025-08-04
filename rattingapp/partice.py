import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class Review(models.Model):
    """
    Model for restaurant reviews with overall and specific ratings
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField()
    session_id = models.UUIDField()
    restaurant_id = models.UUIDField()
    
    # Rating fields (1-5 scale)
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    food_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    service_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    ambiance_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    # Review content
    comment = models.TextField(blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    
    # AI sentiment analysis result (-1 to 1, where -1 is negative, 0 is neutral, 1 is positive)
    sentiment_score = models.DecimalField(
        max_digits=3, decimal_places=2, 
        null=True, blank=True,
        validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant_id']),
            models.Index(fields=['order_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['overall_rating']),
        ]
    
    def __str__(self):
        return f"Review {self.id} - Rating: {self.overall_rating}/5"
    
    @property
    def average_specific_rating(self):
        """Calculate average of food, service, and ambiance ratings"""
        ratings = [r for r in [self.food_rating, self.service_rating, self.ambiance_rating] if r is not None]
        return sum(ratings) / len(ratings) if ratings else None
    
    def get_sentiment_label(self):
        """Convert sentiment score to human-readable label"""
        if self.sentiment_score is None:
            return "Not analyzed"
        elif self.sentiment_score >= 0.1:
            return "Positive"
        elif self.sentiment_score <= -0.1:
            return "Negative"
        else:
            return "Neutral"


class ItemReview(models.Model):
    """
    Model for individual menu item reviews within a restaurant review
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(
        Review, 
        on_delete=models.CASCADE, 
        related_name='item_reviews'
    )
    menu_item_id = models.UUIDField()
    
    # Item rating (1-5 scale)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'item_reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['review_id']),
            models.Index(fields=['menu_item_id']),
            models.Index(fields=['rating']),
        ]
        unique_together = ['review', 'menu_item_id']  # One review per item per order
    
    def __str__(self):
        return f"Item Review {self.id} - Item: {self.menu_item_id} - Rating: {self.rating}/5"


class ReviewAnalytics(models.Model):
    """
    Model for storing aggregated review analytics for restaurants
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant_id = models.UUIDField(unique=True)
    
    # Aggregate ratings
    total_reviews = models.IntegerField(default=0)
    average_overall_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    average_food_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    average_service_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    average_ambiance_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    # Sentiment distribution
    positive_sentiment_count = models.IntegerField(default=0)
    neutral_sentiment_count = models.IntegerField(default=0)
    negative_sentiment_count = models.IntegerField(default=0)
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'review_analytics'
    
    def __str__(self):
        return f"Analytics for Restaurant {self.restaurant_id}"