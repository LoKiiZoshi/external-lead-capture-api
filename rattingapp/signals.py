from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count, Case, When, IntegerField
from django.db.models.functions import Round
from .models import Review, ItemReview, ReviewAnalytics


@receiver(post_save, sender=Review)
def update_analytics_on_review_save(sender, instance, created, **kwargs):
    """
    Update restaurant analytics when a review is saved
    """
    update_restaurant_analytics(instance.restaurant_id)


@receiver(post_delete, sender=Review)
def update_analytics_on_review_delete(sender, instance, **kwargs):
    """
    Update restaurant analytics when a review is deleted
    """
    update_restaurant_analytics(instance.restaurant_id)


def update_restaurant_analytics(restaurant_id):
    """
    Update or create analytics for the specified restaurant
    """
    try:
        reviews = Review.objects.filter(restaurant_id=restaurant_id)
        
        if not reviews.exists():
            # Delete analytics if no reviews left
            ReviewAnalytics.objects.filter(restaurant_id=restaurant_id).delete()
            return
        
        # Calculate aggregates
        analytics_data = reviews.aggregate(
            total_reviews=Count('id'),
            avg_overall=Avg('overall_rating'),
            avg_food=Avg('food_rating'),
            avg_service=Avg('service_rating'),
            avg_ambiance=Avg('ambiance_rating'),
            positive_count=Count(Case(
                When(sentiment_score__gte=0.1, then=1),
                output_field=IntegerField()
            )),
            neutral_count=Count(Case(
                When(sentiment_score__lt=0.1, sentiment_score__gt=-0.1, then=1),
                output_field=IntegerField()
            )),
            negative_count=Count(Case(
                When(sentiment_score__lte=-0.1, then=1),
                output_field=IntegerField()
            ))
        )
        
        # Update or create analytics
        analytics, created = ReviewAnalytics.objects.update_or_create(
            restaurant_id=restaurant_id,
            defaults={
                'total_reviews': analytics_data['total_reviews'],
                'average_overall_rating': Round(analytics_data['avg_overall'] or 0, 2),
                'average_food_rating': Round(analytics_data['avg_food'] or 0, 2) if analytics_data['avg_food'] else None,
                'average_service_rating': Round(analytics_data['avg_service'] or 0, 2) if analytics_data['avg_service'] else None,
                'average_ambiance_rating': Round(analytics_data['avg_ambiance'] or 0, 2) if analytics_data['avg_ambiance'] else None,
                'positive_sentiment_count': analytics_data['positive_count'],
                'neutral_sentiment_count': analytics_data['neutral_count'],
                'negative_sentiment_count': analytics_data['negative_count'],
            }
        )
        
        action = "Created" if created else "Updated"
        print(f"{action} analytics for restaurant {restaurant_id}")
        
    except Exception as e:
        print(f"Error updating analytics for restaurant {restaurant_id}: {e}")


@receiver(post_save, sender=ItemReview)
def log_item_review_creation(sender, instance, created, **kwargs):
    """
    Log when a new item review is created (optional)
    """
    if created:
        print(f"New item review created for menu item {instance.menu_item_id} with rating {instance.rating}")


@receiver(post_delete, sender=ItemReview)
def log_item_review_deletion(sender, instance, **kwargs):
    """
    Log when an item review is deleted (optional)
    """
    print(f"Item review deleted for menu item {instance.menu_item_id}")