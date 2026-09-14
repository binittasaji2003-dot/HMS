/**
 * HRMS Candidate Portal - Notifications JS
 * Handles notification category tabs and mark-all-as-read interaction.
 */

document.addEventListener('DOMContentLoaded', () => {
  initNotificationTabs();
  initMarkAsRead();
});

function initNotificationTabs() {
  const tabs = document.querySelectorAll('.notification-tab-btn');
  const items = document.querySelectorAll('.notification-item-card');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const category = tab.getAttribute('data-category');

      items.forEach(item => {
        if (category === 'all' || item.getAttribute('data-category') === category) {
          item.style.display = 'flex';
        } else {
          item.style.display = 'none';
        }
      });
    });
  });
}

function initMarkAsRead() {
  const markReadBtn = document.getElementById('markAllReadBtn');
  const unreadBadges = document.querySelectorAll('.unread-dot');
  const notificationCards = document.querySelectorAll('.notification-item-card.unread');

  if (markReadBtn) {
    markReadBtn.addEventListener('click', () => {
      unreadBadges.forEach(dot => dot.style.display = 'none');
      notificationCards.forEach(card => card.classList.remove('unread'));

      const headerDot = document.querySelector('.header-badge-dot');
      if (headerDot) headerDot.style.display = 'none';

      const navBadge = document.querySelector('.nav-item[href*="notifications"] .nav-badge');
      if (navBadge) navBadge.style.display = 'none';

      if (window.showToast) {
        window.showToast('Updated', 'All notifications marked as read', 'success');
      }
    });
  }
}
