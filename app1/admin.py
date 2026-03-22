from django.contrib import admin
from .models import Category, Tag, Post, Comment, Event, RSVP, CampusMantri, AboutPage, Achievement, ValueCard, FAQ, \
    ContactMessage, MemberRole, EventPhoto


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ("name", "slug", "color")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display   = ("title", "author", "category", "status", "created_at")
    list_filter    = ("status", "category", "tags")
    search_fields  = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal   = ("tags",)
    date_hierarchy = "created_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ("author", "post", "created_at", "is_active")
    list_filter   = ("is_active",)
    actions       = ["approve_comments", "hide_comments"]

    def approve_comments(self, request, queryset):
        queryset.update(is_active=True)
    approve_comments.short_description = "Approve selected comments"

    def hide_comments(self, request, queryset):
        queryset.update(is_active=False)
    hide_comments.short_description = "Hide selected comments"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display  = ("title", "organizer", "mode", "start_dt", "is_published", "rsvp_count")
    list_filter   = ("mode", "is_published", "category")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal   = ("tags",)

    def rsvp_count(self, obj):
        return obj.rsvp_count
    rsvp_count.short_description = "RSVPs"


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "status", "created_at")
    list_filter  = ("status",)
from django.contrib import admin
from .models import TeamCategory, TeamMember


class TeamMemberInline(admin.TabularInline):
    """Show members directly inside the TeamCategory admin."""
    model        = TeamMember
    extra        = 1
    fields       = ('name', 'role', 'branch', 'year', 'photo', 'is_active', 'order')
    ordering     = ('order', 'name')
    show_change_link = True


@admin.register(TeamCategory)
class TeamCategoryAdmin(admin.ModelAdmin):
    list_display  = ('get_name_display', 'description', 'order')
    list_editable = ('order',)
    ordering      = ('order',)
    inlines       = [TeamMemberInline]

    def get_name_display(self, obj):
        return f"{obj.icon}  {obj.get_name_display()}"
    get_name_display.short_description = "Team"


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display   = ('name', 'role', 'team', 'branch', 'year', 'is_active', 'order')
    list_filter    = ('team', 'is_active', 'year')
    search_fields  = ('name', 'role', 'branch', 'skills')
    list_editable  = ('is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}
    ordering       = ('team__order', 'order', 'name')

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'photo', 'role', 'team', 'bio', 'is_active', 'order')
        }),
        ('Academic Details', {
            'fields': ('branch', 'year', 'cgpa', 'joined_at'),
            'classes': ('collapse',),
        }),
        ('Skills', {
            'fields': ('skills',),
            'description': 'Enter skills separated by commas e.g. Python, React, Figma',
        }),
        ('Social & Professional Links', {
            'fields': ('github', 'linkedin', 'twitter', 'instagram',
                       'portfolio', 'email', 'leetcode', 'gfg_profile'),
            'classes': ('collapse',),
        }),
    )

    @admin.register(CampusMantri)
    class CampusMantriAdmin(admin.ModelAdmin):
        list_display = ('name', 'title', 'branch', 'year', 'is_active', 'order')
        list_editable = ('is_active', 'order')
        search_fields = ('name', 'title', 'branch')
        list_filter = ('is_active',)

        fieldsets = (
            ('Identity', {
                'fields': ('name', 'photo', 'title', 'tagline', 'bio', 'is_active', 'order')
            }),
            ('Academic Details', {
                'fields': ('branch', 'year'),
            }),
            ('Achievements', {
                'fields': ('achievements',),
                'description': 'Enter one achievement per line. They appear as bullet points on the page.',
            }),
            ('Social & Professional Links', {
                'fields': ('github', 'linkedin', 'twitter', 'instagram',
                           'gfg_profile', 'leetcode', 'email', 'portfolio'),
                'classes': ('collapse',),
            }),
        )
from .models import SiteStats

@admin.register(SiteStats)
class SiteStatsAdmin(admin.ModelAdmin):
    list_display = ('members', 'events_hosted', 'articles_published', 'years_running', 'active_teams')

    def has_add_permission(self, request):
        # Prevent adding more than one row
        return not SiteStats.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

# ─────────────────────────────────────────────
# Paste into app1/admin.py
# Add to imports: from .models import ..., AboutPage, Achievement, ValueCard, FAQ
# ─────────────────────────────────────────────

@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Hero Section', {
            'fields': ('hero_tagline', 'hero_heading', 'hero_subtext'),
        }),
        ('Our Story', {
            'fields': ('story_heading', 'story_body'),
            'description': 'Separate paragraphs with a blank line.',
        }),
        ('Vision & Mission', {
            'fields': ('vision_heading', 'vision_text', 'mission_text'),
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_address', 'contact_map_url'),
        }),
        ('Chapter Social Links', {
            'fields': ('social_instagram', 'social_linkedin', 'social_twitter',
                       'social_github', 'social_youtube', 'social_discord'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return not AboutPage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display  = ('title', 'highlight', 'icon', 'date', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    list_filter   = ('is_active',)
    search_fields = ('title', 'description')


@admin.register(ValueCard)
class ValueCardAdmin(admin.ModelAdmin):
    list_display  = ('title', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display  = ('question', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('question', 'answer')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display  = ('name', 'email', 'subject', 'submitted_at', 'is_read')
    list_filter   = ('is_read',)
    search_fields = ('name', 'email', 'subject', 'message')
    list_editable = ('is_read',)
    readonly_fields = ('name', 'email', 'subject', 'message', 'submitted_at')

    def has_add_permission(self, request):
        return False  # messages only come from the form


@admin.register(MemberRole)
class MemberRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active', 'joined_date')
    list_filter = ('role', 'is_active')
    list_editable = ('role', 'is_active')
    search_fields = ('user__username', 'user__email')
    raw_id_fields = ('user',)


class EventPhotoInline(admin.TabularInline):
    model = EventPhoto
    extra = 3
    fields = ('image', 'caption', 'order')


@admin.register(EventPhoto)
class EventPhotoAdmin(admin.ModelAdmin):
    list_display = ('event', 'caption', 'order', 'uploaded_at')
    list_filter = ('event',)
    ordering = ('event', 'order')