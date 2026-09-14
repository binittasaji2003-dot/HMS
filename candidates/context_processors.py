"""Context processors for Candidate portal and notifications."""
from .models import Candidate


def candidate_notifications_context(request):
    """
    Injects real-time unread notifications count and candidate profile
    into all template rendering contexts for authenticated candidates.
    """
    if request.user.is_authenticated:
        try:
            candidate = getattr(request.user, "candidate_profile", None)
            if candidate is None:
                candidate = Candidate.objects.filter(user=request.user).first()
            if candidate:
                unread_count = candidate.notifications.filter(is_read=False).count()
                return {
                    "unread_notifications_count": unread_count,
                    "candidate_profile": candidate,
                }
        except Exception:
            pass
    return {
        "unread_notifications_count": 0,
        "candidate_profile": None,
    }
