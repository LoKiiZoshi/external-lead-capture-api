from django.contrib import admin
from django.db.models import Avg, Count
from django.utils.html import format_html
from .models import Review, ItemReview, ReviewAnalytics


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for Review model
    """
    list_display = [
        'id', 'restaurant_id', 'overall_rating', 'sentiment_display',
        'is_anonymous', 'created_at'
    ]
    list_filter = [
        'overall_rating', 'is_anonymous', 'created_at',
        'food_rating', 'service_rating', 'ambiance_rating'
    ]
    search_fields = ['restaurant_id', 'comment', 'order_id']
    readonly_fields = ['id', 'sentiment_score', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'order_id', 'session_id', 'restaurant_id')
        }),
        ('Ratings', {
            'fields': ('overall_rating', 'food_rating', 'service_rating', 'ambiance_rating')
        }),
        ('Review Content', {
            'fields': ('comment', 'is_anonymous', 'sentiment_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def sentiment_display(self, obj):
        """Display sentiment with color coding"""
        if obj.sentiment_score is None:
            return format_html('<span style="color: gray;">Not analyzed</span>')
        elif obj.sentiment_score >= 0.1:
            return format_html('<span style="color: green;">Positive ({:.2f})</span>', obj.sentiment_score)
        elif obj.sentiment_score <= -0.1:
            return format_html('<span style="color: red;">Negative ({:.2f})</span>', obj.sentiment_score)
        else:
            return format_html('<span style="color: orange;">Neutral ({:.2f})</span>', obj.sentiment_score)
    
    sentiment_display.short_description = 'Sentiment'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related"""
        return super().get_queryset(request).prefetch_related('item_reviews')


@admin.register(ItemReview)
class ItemReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for ItemReview model
    """
    list_display = ['id', 'review', 'menu_item_id', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['menu_item_id', 'comment', 'review__restaurant_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'review', 'menu_item_id')
        }),
        ('Review Details', {
            'fields': ('rating', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ReviewAnalytics)
class ReviewAnalyticsAdmin(admin.ModelAdmin):
    """
    Admin interface for ReviewAnalytics model
    """
    list_display = [
        'restaurant_id', 'total_reviews', 'average_overall_rating',
        'sentiment_summary', 'last_updated'
    ]
    list_filter = ['last_updated']
    search_fields = ['restaurant_id']
    readonly_fields = [
        'id', 'restaurant_id', 'total_reviews', 'average_overall_rating',
        'average_food_rating', 'average_service_rating', 'average_ambiance_rating',
        'positive_sentiment_count', 'neutral_sentiment_count', 'negative_sentiment_count',
        'last_updated'
    ]
    
    fieldsets = (
        ('Restaurant Information', {
            'fields': ('id', 'restaurant_id')
        }),
        ('Review Statistics', {
            'fields': ('total_reviews', 'average_overall_rating')
        }),
        ('Detailed Ratings', {
            'fields': ('average_food_rating', 'average_service_rating', 'average_ambiance_rating')
        }),
        ('Sentiment Analysis', {
            'fields': ('positive_sentiment_count', 'neutral_sentiment_count', 'negative_sentiment_count')
        }),
        ('Metadata', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        })
    )
    
    def sentiment_summary(self, obj):
        """Display sentiment distribution summary"""
        total = obj.total_reviews
        if total == 0:
            return "No reviews"
        
        positive_pct = round((obj.positive_sentiment_count / total) * 100, 1)
        neutral_pct = round((obj.neutral_sentiment_count / total) * 100, 1)
        negative_pct = round((obj.negative_sentiment_count / total) * 100, 1)
        
        return format_html(
            '<span style="color: green;">{positive}%</span> | '
            '<span style="color: orange;">{neutral}%</span> | '
            '<span style="color: red;">{negative}%</span>',
            positive=positive_pct,
            neutral=neutral_pct,
            negative=negative_pct
        )
    
    sentiment_summary.short_description = 'Sentiment Distribution'
    
    def has_add_permission(self, request):
        """Disable manual creation of analytics (should be auto-generated)"""
        return False


# Custom admin site configurations
class ReviewAdminSite(admin.AdminSite):
    """
    Custom admin site for review management
    """
    site_header = "Restaurant Review Management"
    site_title = "Review Admin"
    index_title = "Welcome to Review Administration"


# Optional: Create custom admin site instance
# review_admin_site = ReviewAdminSite(name='reviewadmin')
# review_admin_site.register(Review, ReviewAdmin)
# review_admin_site.register(ItemReview, ItemReviewAdmin)
# review_admin_site.register(ReviewAnalytics, ReviewAnalyticsAdmin)