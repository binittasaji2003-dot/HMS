"""Context processors for the Candidates app."""

def candidate_notifications(request):
    """Expose candidate notification counters, recent notifications, and unread decision popup to templates."""
    if not request.user.is_authenticated:
        return {}

    candidate = getattr(request.user, "candidate_profile", None)
    if not candidate:
        return {}

    notifications_qs = (
        candidate.notifications.select_related("application", "application__vacancy", "application__screening_result")
        .all()
    )
    unread_count = notifications_qs.filter(is_read=False).count()
    recent_notifications = notifications_qs[:5]

    # Find the latest unread popup notification for modal popup
    popup_notification = notifications_qs.filter(
        is_read=False,
        notification_type__in=[
            "APPLICATION_SUBMITTED",
            "SHORTLISTED",
            "NOT_SHORTLISTED",
            "APTITUDE_SCHEDULED",
            "APTITUDE_RESCHEDULED",
            "APTITUDE_CANCELLED",
            "INTERVIEW_ELIGIBLE",
            "INTERVIEW_SCHEDULED",
            "INTERVIEW_PASSED",
            "EMPLOYEE_CONVERTED",
        ],
    ).first()

    return {
        "candidate_unread_notifications_count": unread_count,
        "candidate_recent_notifications": recent_notifications,
        "candidate_popup_notification": popup_notification,
    }

