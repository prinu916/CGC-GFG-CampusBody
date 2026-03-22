from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse


# ─────────────────────────────────────────────
#  SHARED
# ─────────────────────────────────────────────

class Category(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    color       = models.CharField(max_length=7, default="#2F8D46")  # GFG green

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────
#  BLOG
# ─────────────────────────────────────────────

class Post(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("published", "Published")]

    title       = models.CharField(max_length=250)
    slug        = models.SlugField(unique=True, blank=True, max_length=300)
    author      = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    tags        = models.ManyToManyField(Tag, blank=True, related_name="posts")
    content     = models.TextField()          # store Markdown here
    excerpt     = models.TextField(blank=True, max_length=300)
    cover_image = models.ImageField(upload_to="blog/covers/", blank=True, null=True)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title


class Comment(models.Model):
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author     = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active  = models.BooleanField(default=True)   # admin can hide spam

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username} on '{self.post.title}'"


# ─────────────────────────────────────────────
#  EVENTS
# ─────────────────────────────────────────────

class Event(models.Model):
    MODE_CHOICES = [("online", "Online"), ("offline", "Offline"), ("hybrid", "Hybrid")]

    title        = models.CharField(max_length=250)
    slug         = models.SlugField(unique=True, blank=True, max_length=300)
    organizer    = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events")
    category     = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    tags         = models.ManyToManyField(Tag, blank=True, related_name="events")
    description  = models.TextField()         # Markdown supported
    cover_image  = models.ImageField(upload_to="events/covers/", blank=True, null=True)
    mode         = models.CharField(max_length=10, choices=MODE_CHOICES, default="offline")
    venue        = models.CharField(max_length=300, blank=True)   # blank for online
    meet_link    = models.URLField(blank=True)                    # blank for offline
    start_dt     = models.DateTimeField()
    end_dt       = models.DateTimeField()
    max_rsvp     = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    is_published = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_dt"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("event_detail", kwargs={"slug": self.slug})

    @property
    def rsvp_count(self):
        return self.rsvps.filter(status="going").count()

    @property
    def seats_left(self):
        if self.max_rsvp == 0:
            return None          # unlimited
        return max(0, self.max_rsvp - self.rsvp_count)

    @property
    def is_full(self):
        return self.max_rsvp > 0 and self.rsvp_count >= self.max_rsvp

    def __str__(self):
        return self.title


class EventPhoto(models.Model):
    """Multiple photos for a single event — scrollable gallery."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='event_photos/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'uploaded_at']
        verbose_name = 'Event Photo'
        verbose_name_plural = 'Event Photos'

    def __str__(self):
        return f"{self.event.title} — Photo {self.order}"

class RSVP(models.Model):
    STATUS_CHOICES = [("going", "Going"), ("not_going", "Not Going")]

    event      = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rsvps")
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rsvps")
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default="going")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "user")   # one RSVP per user per event

    def __str__(self):
        return f"{self.user.username} → {self.event.title} ({self.status})"

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# ─────────────────────────────────────────────
#  EXISTING MODELS (Category, Tag, Post, Comment, Event, RSVP)
#  ... keep all your existing models above this
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
#  TEAM
# ─────────────────────────────────────────────

class TeamCategory(models.Model):
    """Represents a team division e.g. Tech Team, PR Team etc."""

    CATEGORY_CHOICES = [
        ('management',   'Management Team'),
        ('tech',         'Tech Team'),
        ('pr',           'PR Team'),
        ('social_media', 'Social Media Team'),
        ('design',       'Designing Team'),
        ('core',         'Core Member Team'),
    ]

    # Preset icon & gradient for each team type
    TEAM_META = {
        'management':   {'icon': '👑', 'gradient': 'linear-gradient(135deg,#f8b400,#e65c00)', 'color': '#f8b400'},
        'tech':         {'icon': '⚙️', 'gradient': 'linear-gradient(135deg,#00ff87,#00c9ff)', 'color': '#00ff87'},
        'pr':           {'icon': '📢', 'gradient': 'linear-gradient(135deg,#f953c6,#b91d73)', 'color': '#f953c6'},
        'social_media': {'icon': '📱', 'gradient': 'linear-gradient(135deg,#4facfe,#00f2fe)', 'color': '#4facfe'},
        'design':       {'icon': '🎨', 'gradient': 'linear-gradient(135deg,#a18cd1,#fbc2eb)', 'color': '#a18cd1'},
        'core':         {'icon': '⭐', 'gradient': 'linear-gradient(135deg,#2F8D46,#00ff87)',  'color': '#2F8D46'},
    }

    name = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True, help_text="Short description shown on the team page")
    order       = models.PositiveSmallIntegerField(default=0, help_text="Lower = shown first")

    class Meta:
        ordering = ['order', 'name']
        verbose_name        = "Team Category"
        verbose_name_plural = "Team Categories"

    def __str__(self):
        return self.get_name_display()

    @property
    def icon(self):
        return self.TEAM_META.get(self.name, {}).get('icon', '👤')

    @property
    def gradient(self):
        return self.TEAM_META.get(self.name, {}).get('gradient', 'linear-gradient(135deg,#2F8D46,#00ff87)')

    @property
    def color(self):
        return self.TEAM_META.get(self.name, {}).get('color', '#2F8D46')


class TeamMember(models.Model):
    """A single team member with all credentials."""

    # Basic info
    name       = models.CharField(max_length=150)
    slug       = models.SlugField(unique=True, blank=True, max_length=200)
    photo      = models.ImageField(upload_to='team/photos/', blank=True, null=True,
                                   help_text="Square image recommended (300×300px+)")
    role       = models.CharField(max_length=150, help_text="e.g. Team Lead, Frontend Dev")
    team       = models.ForeignKey(TeamCategory, on_delete=models.CASCADE, related_name='members')
    bio        = models.TextField(blank=True, help_text="Short bio (2–3 sentences)")

    # Academic info
    branch     = models.CharField(max_length=100, blank=True, help_text="e.g. Computer Science")
    year       = models.CharField(max_length=20,  blank=True, help_text="e.g. 2nd Year, Batch 2025")
    cgpa       = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # Social / professional links
    github     = models.URLField(blank=True)
    linkedin   = models.URLField(blank=True)
    twitter    = models.URLField(blank=True)
    instagram  = models.URLField(blank=True)
    portfolio  = models.URLField(blank=True, help_text="Personal website or portfolio")
    email      = models.EmailField(blank=True)
    leetcode   = models.URLField(blank=True)
    gfg_profile= models.URLField(blank=True, help_text="GeeksForGeeks profile URL")

    # Skills (comma-separated)
    skills     = models.CharField(max_length=500, blank=True,
                                  help_text="Comma-separated e.g. Python, Django, React")

    # Visibility & ordering
    is_active  = models.BooleanField(default=True, help_text="Uncheck to hide from the page")
    order      = models.PositiveSmallIntegerField(default=0, help_text="Lower = shown first within team")
    joined_at  = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['team__order', 'order', 'name']
        verbose_name        = "Team Member"
        verbose_name_plural = "Team Members"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} — {self.role} ({self.team})"

    def get_initials(self):
        parts = self.name.strip().split()
        if len(parts) >= 2:
            return parts[0][0].upper() + parts[-1][0].upper()
        return self.name[:2].upper()

    def get_skills_list(self):
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    def has_social(self):
        return any([self.github, self.linkedin, self.twitter,
                    self.instagram, self.portfolio, self.gfg_profile])


class CampusMantri(models.Model):
    """
    Special highlighted role — Campus Mantri / Ambassador.
    Displayed as a featured column on the home page.
    """
    name = models.CharField(max_length=150)
    photo = models.ImageField(upload_to='campus_mantri/', blank=True, null=True,
                              help_text="Square image recommended (400×400px+)")
    title = models.CharField(max_length=150, default="Campus Mantri",
                             help_text="e.g. Campus Mantri, GFG Campus Ambassador")
    tagline = models.CharField(max_length=220, blank=True,
                               help_text="Short inspiring line shown below the name")
    bio = models.TextField(blank=True,
                           help_text="Full bio shown on the home page card")
    branch = models.CharField(max_length=100, blank=True)
    year = models.CharField(max_length=30, blank=True)

    # Achievements / highlights (comma-separated)
    achievements = models.TextField(blank=True,
                                    help_text="One achievement per line. Shown as bullet points.")

    # Social / professional links
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    gfg_profile = models.URLField(blank=True)
    leetcode = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    portfolio = models.URLField(blank=True)

    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0,
                                             help_text="Lower = shown first")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Campus Mantri"
        verbose_name_plural = "Campus Mantris"

    def __str__(self):
        return f"{self.name} — {self.title}"

    def get_initials(self):
        parts = self.name.strip().split()
        if len(parts) >= 2:
            return parts[0][0].upper() + parts[-1][0].upper()
        return self.name[:2].upper()

    def get_achievements_list(self):
        return [a.strip() for a in self.achievements.splitlines() if a.strip()]
class SiteStats(models.Model):
    members          = models.PositiveIntegerField(default=500)
    events_hosted    = models.PositiveIntegerField(default=40)
    articles_published = models.PositiveIntegerField(default=100)
    years_running    = models.PositiveIntegerField(default=3)
    active_teams     = models.PositiveIntegerField(default=6)

    class Meta:
        verbose_name        = "Site Statistics"
        verbose_name_plural = "Site Statistics"

    def __str__(self):
        return "Site Statistics"

    def save(self, *args, **kwargs):
        # Only allow one row ever
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
# ─────────────────────────────────────────────
# Add all these to the BOTTOM of app1/models.py
# ─────────────────────────────────────────────

class AboutPage(models.Model):
    """Single-row model for the main About page content."""

    # Hero
    hero_tagline    = models.CharField(max_length=120, default="About Us",
                                       help_text="Small label above the heading")
    hero_heading    = models.CharField(max_length=220, default="We Are GFG CGC Chapter",
                                       help_text="Main big heading")
    hero_subtext    = models.TextField(blank=True,
                                       help_text="Paragraph shown below the heading")

    # Story / Who we are
    story_heading   = models.CharField(max_length=150, default="Our Story")
    story_body      = models.TextField(blank=True,
                                       help_text="Multi-paragraph story. Use blank lines to separate paragraphs.")

    # Vision & Mission
    vision_heading  = models.CharField(max_length=150, default="Vision & Mission")
    vision_text     = models.TextField(blank=True, help_text="Vision statement")
    mission_text    = models.TextField(blank=True, help_text="Mission statement")

    # Contact info
    contact_email   = models.EmailField(blank=True)
    contact_phone   = models.CharField(max_length=20, blank=True)
    contact_address = models.TextField(blank=True,
                                       help_text="Full address shown on contact section")
    contact_map_url = models.URLField(blank=True,
                                      help_text="Google Maps embed URL for contact section")

    # Social links (chapter-level)
    social_instagram  = models.URLField(blank=True)
    social_linkedin   = models.URLField(blank=True)
    social_twitter    = models.URLField(blank=True)
    social_github     = models.URLField(blank=True)
    social_youtube    = models.URLField(blank=True)
    social_discord    = models.URLField(blank=True)

    class Meta:
        verbose_name        = "About Page"
        verbose_name_plural = "About Page"

    def __str__(self):
        return "About Page Content"

    def save(self, *args, **kwargs):
        self.pk = 1   # singleton
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def get_story_paragraphs(self):
        return [p.strip() for p in self.story_body.split('\n\n') if p.strip()]


class Achievement(models.Model):
    """An award, recognition, or milestone shown on the About page."""

    ICON_CHOICES = [
        ('🏆', '🏆 Trophy'),
        ('🥇', '🥇 Gold Medal'),
        ('🎖️', '🎖️ Medal'),
        ('⭐', '⭐ Star'),
        ('🚀', '🚀 Rocket'),
        ('💡', '💡 Bulb'),
        ('🌟', '🌟 Glowing Star'),
        ('🎯', '🎯 Target'),
        ('📢', '📢 Megaphone'),
        ('🤝', '🤝 Handshake'),
        ('💻', '💻 Laptop'),
        ('🌐', '🌐 Globe'),
    ]

    title       = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=10, choices=ICON_CHOICES, default='🏆')
    date        = models.DateField(null=True, blank=True,
                                   help_text="When this was achieved")
    highlight   = models.CharField(max_length=80, blank=True,
                                   help_text="Short bold stat e.g. '1st Place', '500+ attendees'")
    is_active   = models.BooleanField(default=True)
    order       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering            = ['order', '-date']
        verbose_name        = "Achievement"
        verbose_name_plural = "Achievements"

    def __str__(self):
        return self.title


class ValueCard(models.Model):
    """Core values / principles shown on the About page."""

    ICON_CHOICES = [
        ('⚡', '⚡ Lightning'),
        ('🤝', '🤝 Handshake'),
        ('💡', '💡 Bulb'),
        ('🌱', '🌱 Seedling'),
        ('🔥', '🔥 Fire'),
        ('🧠', '🧠 Brain'),
        ('🎯', '🎯 Target'),
        ('🌐', '🌐 Globe'),
        ('💎', '💎 Diamond'),
        ('🚀', '🚀 Rocket'),
    ]

    title       = models.CharField(max_length=100)
    description = models.TextField()
    icon        = models.CharField(max_length=10, choices=ICON_CHOICES, default='💡')
    order       = models.PositiveSmallIntegerField(default=0)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering            = ['order']
        verbose_name        = "Core Value"
        verbose_name_plural = "Core Values"

    def __str__(self):
        return self.title


class FAQ(models.Model):
    """Frequently asked questions shown on the About page."""

    question    = models.CharField(max_length=300)
    answer      = models.TextField()
    order       = models.PositiveSmallIntegerField(default=0)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering            = ['order']
        verbose_name        = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question

class ContactMessage(models.Model):
    name       = models.CharField(max_length=150)
    email      = models.EmailField()
    subject    = models.CharField(max_length=300, blank=True)
    message    = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_read    = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name        = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} — {self.subject or 'No subject'}"


class MemberRole(models.Model):
    """
    Roles that control what a member can do in the dashboard.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),  # full access
        ('blog_editor', 'Blog Editor'),  # blog only
        ('event_manager', 'Event Manager'),  # events only
        ('team_manager', 'Team Manager'),  # team members only
        ('moderator', 'Moderator'),  # blog + events (read/edit, no delete)
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_role')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='blog_editor')
    is_active = models.BooleanField(default=True, help_text="Uncheck to revoke dashboard access")
    joined_date = models.DateField(auto_now_add=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='member_avatars/', blank=True, null=True)

    class Meta:
        verbose_name = "Member Role"
        verbose_name_plural = "Member Roles"

    def __str__(self):
        return f"{self.user.username} — {self.get_role_display()}"

    # ── permission helpers ──
    @property
    def can_manage_blog(self):
        return self.role in ('admin', 'blog_editor', 'moderator')

    @property
    def can_manage_events(self):
        return self.role in ('admin', 'event_manager', 'moderator')

    @property
    def can_manage_team(self):
        return self.role in ('admin', 'team_manager')

    @property
    def can_delete(self):
        return self.role == 'admin'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def role_color(self):
        colors = {
            'admin': '#f8b400',
            'blog_editor': '#00ff87',
            'event_manager': '#60a5fa',
            'team_manager': '#a78bfa',
            'moderator': '#fb923c',
        }
        return colors.get(self.role, '#7d8590')

    @property
    def role_icon(self):
        icons = {
            'admin': '👑',
            'blog_editor': '✍️',
            'event_manager': '🗓️',
            'team_manager': '👥',
            'moderator': '🛡️',
        }
        return icons.get(self.role, '👤')