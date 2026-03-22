# ─────────────────────────────────────────────
# FILE 1:  gfg_cgc/urls.py   (your project-level urls.py)
# ─────────────────────────────────────────────

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app1.urls')),          # all app routes come from app1/urls.py
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# ─────────────────────────────────────────────
# FILE 2:  app1/urls.py   (create this new file)
# ─────────────────────────────────────────────

from django.urls import path
from . import views


urlpatterns = [
    # Home
    path('',                            views.index,        name='index'),

    # Blog
    path('blog/',                       views.blog_list,    name='blog_list'),
    path('blog/<slug:slug>/',           views.post_detail,  name='post_detail'),

    # Events
    path('events/',                     views.event_list,   name='event_list'),
    path('events/<slug:slug>/',         views.event_detail, name='event_detail'),
    path('events/<slug:slug>/rsvp/',    views.rsvp_toggle,  name='rsvp_toggle'),

    # Search
    path('search/',                     views.search,       name='search'),
    path('team/', views.team_page, name='team_page'),
    path('about/', views.about_page, name='about_page'),
    path('dashboard/login/', views.dashboard_login, name='dashboard_login'),
    path('dashboard/logout/', views.dashboard_logout, name='dashboard_logout'),

    # ── Dashboard Home ──
    path('dashboard/', views.dashboard_home, name='dashboard_home'),

    # ── Blog ──
    path('dashboard/blogs/', views.dashboard_blogs, name='dashboard_blogs'),
    path('dashboard/blogs/create/', views.dashboard_blog_create, name='dashboard_blog_create'),
    path('dashboard/blogs/<int:pk>/edit/', views.dashboard_blog_edit, name='dashboard_blog_edit'),
    path('dashboard/blogs/<int:pk>/delete/', views.dashboard_blog_delete, name='dashboard_blog_delete'),

    # ── Events ──
    path('dashboard/events/', views.dashboard_events, name='dashboard_events'),
    path('dashboard/events/create/', views.dashboard_event_create, name='dashboard_event_create'),
    path('dashboard/events/<int:pk>/edit/', views.dashboard_event_edit, name='dashboard_event_edit'),
    path('dashboard/events/<int:pk>/delete/', views.dashboard_event_delete, name='dashboard_event_delete'),

    # ── Team ──
    path('dashboard/team/', views.dashboard_team, name='dashboard_team'),
    path('dashboard/team/<int:pk>/toggle/', views.dashboard_team_toggle, name='dashboard_team_toggle'),

    # ── Comments ──
    path('dashboard/comments/', views.dashboard_comments, name='dashboard_comments'),
    path('dashboard/comments/<int:pk>/toggle/', views.dashboard_comment_toggle, name='dashboard_comment_toggle'),
path('dashboard/team/create/',         views.dashboard_team_create, name='dashboard_team_create'),
    path('dashboard/team/<int:pk>/edit/',  views.dashboard_team_edit,   name='dashboard_team_edit'),
    path('dashboard/team/<int:pk>/delete/',views.dashboard_team_delete, name='dashboard_team_delete'),
    path('dashboard/about/', views.dashboard_about, name='dashboard_about'),
    path('dashboard/about/edit/', views.dashboard_about_edit, name='dashboard_about_edit'),

    # ── Achievements ──
    path('dashboard/about/achievements/add/', views.dashboard_achievement_create, name='dashboard_achievement_create'),
    path('dashboard/about/achievements/<int:pk>/edit/', views.dashboard_achievement_edit,
         name='dashboard_achievement_edit'),
    path('dashboard/about/achievements/<int:pk>/delete/', views.dashboard_achievement_delete,
         name='dashboard_achievement_delete'),

    # ── Core Values ──
    path('dashboard/about/values/add/', views.dashboard_value_create, name='dashboard_value_create'),
    path('dashboard/about/values/<int:pk>/edit/', views.dashboard_value_edit, name='dashboard_value_edit'),
    path('dashboard/about/values/<int:pk>/delete/', views.dashboard_value_delete, name='dashboard_value_delete'),

    # ── FAQs ──
    path('dashboard/about/faqs/add/', views.dashboard_faq_create, name='dashboard_faq_create'),
    path('dashboard/about/faqs/<int:pk>/edit/', views.dashboard_faq_edit, name='dashboard_faq_edit'),
    path('dashboard/about/faqs/<int:pk>/delete/', views.dashboard_faq_delete, name='dashboard_faq_delete'),

    # ── Contact Messages ──
    path('dashboard/about/contacts/', views.dashboard_contacts, name='dashboard_contacts'),
    path('dashboard/about/contacts/<int:pk>/read/', views.dashboard_contact_read, name='dashboard_contact_read'),
    path('dashboard/about/contacts/<int:pk>/delete/', views.dashboard_contact_delete, name='dashboard_contact_delete'),
path('dashboard/events/<int:pk>/photos/',                    views.dashboard_event_photos,       name='dashboard_event_photos'),
    path('dashboard/events/<int:pk>/photos/<int:photo_pk>/delete/', views.dashboard_event_photo_delete, name='dashboard_event_photo_delete'),
]