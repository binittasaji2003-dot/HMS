"""Context processors for the Candidates app."""

def candidate_notifications(request):
    """Expose candidate notification counters and recent notifications to templates."""
    if not request.user.is_authenticated:
        return {}

    candidate = getattr(request.user, "candidate_profile", None)
    if not candidate:
        return {}

    notifications_qs = candidate.notifications.all()
    unread_count = notifications_qs.filter(is_read=False).count()
    recent_notifications = notifications_qs[:5]

    return {
        "candidate_unread_notifications_count": unread_count,
        "candidate_recent_notifications": recent_notifications,
    }

