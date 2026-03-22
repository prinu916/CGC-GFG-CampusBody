from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Post, Comment, Event, RSVP, Category, Tag, CampusMantri, AboutPage, Achievement, ValueCard, FAQ, \
    SiteStats, ContactMessage


# ─────────────────────────────────────────────
#  HOME
def index(request):
    from .models import Post, Event, TeamMember, CampusMantri, SiteStats

    recent_posts    = Post.objects.filter(status="published").order_by("-created_at")[:3]
    upcoming_events = Event.objects.filter(is_published=True).order_by("start_dt")[:3]
    core_members    = TeamMember.objects.filter(team__name="core", is_active=True).order_by("order")[:6]
    campus_mantris  = CampusMantri.objects.filter(is_active=True).order_by("order")
    stats           = SiteStats.get()   # ← always returns the one row

    return render(request, "home.html", {
        "recent_posts":    recent_posts,
        "upcoming_events": upcoming_events,
        "core_members":    core_members,
        "campus_mantris":  campus_mantris,
        "stats":           stats,
    })
# ─────────────────────────────────────────────
#  BLOG VIEWS
# ─────────────────────────────────────────────

def blog_list(request):
    posts = Post.objects.filter(status="published")

    # Filter by category
    category_slug = request.GET.get("category")
    if category_slug:
        posts = posts.filter(category__slug=category_slug)

    # Filter by tag
    tag_slug = request.GET.get("tag")
    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)

    categories = Category.objects.all()
    tags       = Tag.objects.all()

    return render(request, "blog/blog_list.html", {
        "posts":      posts,
        "categories": categories,
        "tags":       tags,
        "selected_category": category_slug,
        "selected_tag":      tag_slug,
    })


def post_detail(request, slug):
    post     = get_object_or_404(Post, slug=slug, status="published")
    comments = post.comments.filter(is_active=True)

    # Handle new comment submission
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to comment.")
            return redirect("post_detail", slug=slug)

        body = request.POST.get("body", "").strip()
        if body:
            Comment.objects.create(post=post, author=request.user, body=body)
            messages.success(request, "Comment posted!")
        else:
            messages.error(request, "Comment cannot be empty.")
        return redirect("post_detail", slug=slug)

    related_posts = Post.objects.filter(
        status="published", category=post.category
    ).exclude(pk=post.pk)[:3]

    return render(request, "blog/post_detail.html", {
        "post":          post,
        "comments":      comments,
        "related_posts": related_posts,
    })


# ─────────────────────────────────────────────
#  EVENT VIEWS
# ─────────────────────────────────────────────

def event_list(request):
    events = Event.objects.filter(is_published=True)

    # Filter by category
    category_slug = request.GET.get("category")
    if category_slug:
        events = events.filter(category__slug=category_slug)

    # Filter by tag
    tag_slug = request.GET.get("tag")
    if tag_slug:
        events = events.filter(tags__slug=tag_slug)

    # Filter by mode (online/offline/hybrid)
    mode = request.GET.get("mode")
    if mode:
        events = events.filter(mode=mode)

    categories = Category.objects.all()
    tags       = Tag.objects.all()

    return render(request, "events/event_list.html", {
        "events":      events,
        "categories":  categories,
        "tags":        tags,
        "selected_category": category_slug,
        "selected_tag":      tag_slug,
        "selected_mode":     mode,
    })


def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug, is_published=True)

    user_rsvp = None
    if request.user.is_authenticated:
        user_rsvp = RSVP.objects.filter(event=event, user=request.user).first()

    return render(request, "events/event_detail.html", {
        "event":     event,
        "user_rsvp": user_rsvp,
    })


@login_required
def rsvp_toggle(request, slug):
    """Toggle RSVP: going ↔ not_going, or create new."""
    event = get_object_or_404(Event, slug=slug, is_published=True)

    rsvp, created = RSVP.objects.get_or_create(
        event=event, user=request.user,
        defaults={"status": "going"}
    )

    if not created:
        # Already exists — toggle status
        if rsvp.status == "going":
            if event.is_full:
                messages.error(request, "Sorry, this event is full!")
            else:
                rsvp.status = "not_going"
                rsvp.save()
                messages.info(request, "You've cancelled your RSVP.")
        else:
            rsvp.status = "going"
            rsvp.save()
            messages.success(request, "You're going! See you there 🎉")
    else:
        if event.is_full:
            rsvp.delete()
            messages.error(request, "Sorry, this event is full!")
        else:
            messages.success(request, "RSVP confirmed! See you there 🎉")

    return redirect("event_detail", slug=slug)


# ─────────────────────────────────────────────
#  SEARCH
# ─────────────────────────────────────────────

def search(request):
    query  = request.GET.get("q", "").strip()
    posts  = Post.objects.none()
    events = Event.objects.none()

    if query:
        posts = Post.objects.filter(
            status="published"
        ).filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__name__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()

        events = Event.objects.filter(
            is_published=True
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()

    return render(request, "search.html", {
        "query":  query,
        "posts":  posts,
        "events": events,
        "total":  posts.count() + events.count(),
    })
from django.shortcuts import render, get_object_or_404
from .models import TeamCategory, TeamMember


def team_page(request):
    """
    Renders the full team page grouped by TeamCategory.
    Only active members are shown.
    """
    categories = TeamCategory.objects.prefetch_related(
        'members'
    ).all()

    # Build structured data: [ {category, members, count}, ... ]
    team_sections = []
    total_members = 0

    for cat in categories:
        members = cat.members.filter(is_active=True).order_by('order', 'name')
        if members.exists():
            team_sections.append({
                'category': cat,
                'members':  members,
                'count':    members.count(),
            })
            total_members += members.count()

    return render(request, 'team/team.html', {
        'team_sections': team_sections,
        'total_members': total_members,
    })

from django.contrib import messages as django_messages

def about_page(request):
    from .models import AboutPage, Achievement, ValueCard, FAQ, SiteStats, ContactMessage

    # Handle form POST
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            ContactMessage.objects.create(
                name=name, email=email,
                subject=subject, message=message
            )
            django_messages.success(request, '✅ Message sent! We\'ll get back to you soon.')
        else:
            django_messages.error(request, '❌ Please fill in all required fields.')

        return redirect('about_page')

    about        = AboutPage.get()
    achievements = Achievement.objects.filter(is_active=True).order_by('order', '-date')
    values       = ValueCard.objects.filter(is_active=True).order_by('order')
    faqs         = FAQ.objects.filter(is_active=True).order_by('order')
    stats        = SiteStats.get()

    return render(request, 'about.html', {
        'about':        about,
        'achievements': achievements,
        'values':       values,
        'faqs':         faqs,
        'stats':        stats,
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from .models import (
    Post, Event, TeamMember, TeamCategory,
    Category, Tag, Comment, RSVP, MemberRole, SiteStats
)


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def get_member_role(user):
    """Return MemberRole if user has active access, else None."""
    try:
        role = user.member_role
        return role if role.is_active else None
    except MemberRole.DoesNotExist:
        return None


def member_required(view_func):
    """Decorator: must be logged in + have an active MemberRole."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dashboard_login')
        role = get_member_role(request.user)
        if not role:
            messages.error(request, 'You do not have dashboard access.')
            return redirect('dashboard_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*roles):
    """Decorator: user must have one of the specified roles."""
    from functools import wraps
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('dashboard_login')
            role = get_member_role(request.user)
            if not role or role.role not in roles + ('admin',):
                messages.error(request, 'You do not have permission for this action.')
                return redirect('dashboard_home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────

def dashboard_login(request):
    if request.user.is_authenticated and get_member_role(request.user):
        return redirect('dashboard_home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user:
            role = get_member_role(user)
            if role:
                login(request, user)
                return redirect(request.GET.get('next', 'dashboard_home'))
            else:
                messages.error(request, 'You do not have dashboard access. Contact the admin.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'dashboard/login.html')


@login_required
def dashboard_logout(request):
    logout(request)
    return redirect('dashboard_login')


# ─────────────────────────────────────────────
#  HOME — ANALYTICS OVERVIEW
# ─────────────────────────────────────────────

@member_required
def dashboard_home(request):
    role    = get_member_role(request.user)
    stats   = SiteStats.get()
    now     = timezone.now()

    # counts
    total_posts    = Post.objects.count()
    published_posts= Post.objects.filter(status='published').count()
    draft_posts    = Post.objects.filter(status='draft').count()
    total_events   = Event.objects.count()
    upcoming_events= Event.objects.filter(start_dt__gte=now).count()
    total_members  = TeamMember.objects.filter(is_active=True).count()
    total_comments = Comment.objects.count()
    total_rsvps    = RSVP.objects.filter(status='going').count()

    # recent activity
    recent_posts   = Post.objects.order_by('-created_at')[:5]
    recent_events  = Event.objects.order_by('-created_at')[:5]
    recent_comments= Comment.objects.order_by('-created_at')[:5]

    # blog by category chart data
    cat_data = list(
        Category.objects.annotate(post_count=Count('posts'))
        .values('name', 'post_count').order_by('-post_count')[:6]
    )

    return render(request, 'dashboard/home.html', {
        'role':             role,
        'stats':            stats,
        'total_posts':      total_posts,
        'published_posts':  published_posts,
        'draft_posts':      draft_posts,
        'total_events':     total_events,
        'upcoming_events':  upcoming_events,
        'total_members':    total_members,
        'total_comments':   total_comments,
        'total_rsvps':      total_rsvps,
        'recent_posts':     recent_posts,
        'recent_events':    recent_events,
        'recent_comments':  recent_comments,
        'cat_data':         cat_data,
    })


# ─────────────────────────────────────────────
#  BLOG MANAGEMENT
# ─────────────────────────────────────────────

@member_required
def dashboard_blogs(request):
    role = get_member_role(request.user)
    if not role.can_manage_blog:
        messages.error(request, 'No blog access.')
        return redirect('dashboard_home')

    q      = request.GET.get('q', '')
    status = request.GET.get('status', '')
    posts  = Post.objects.all()

    # non-admins see only their own posts
    if not role.is_admin:
        posts = posts.filter(author=request.user)

    if q:      posts = posts.filter(Q(title__icontains=q) | Q(content__icontains=q))
    if status: posts = posts.filter(status=status)

    posts = posts.order_by('-created_at')
    return render(request, 'dashboard/blogs.html', {
        'role': role, 'posts': posts, 'q': q, 'status_filter': status,
    })


@member_required
def dashboard_blog_create(request):
    role = get_member_role(request.user)
    if not role.can_manage_blog:
        return redirect('dashboard_home')

    categories = Category.objects.all()
    tags       = Tag.objects.all()

    if request.method == 'POST':
        title    = request.POST.get('title', '').strip()
        content  = request.POST.get('content', '').strip()
        excerpt  = request.POST.get('excerpt', '').strip()
        cat_id   = request.POST.get('category')
        tag_ids  = request.POST.getlist('tags')
        status   = request.POST.get('status', 'draft')

        # non-editors can only save drafts
        if not role.is_admin and status == 'published':
            status = 'draft'
            messages.info(request, 'Post saved as draft — only admins can publish directly.')

        if title and content:
            post = Post.objects.create(
                title=title, content=content, excerpt=excerpt,
                author=request.user, status=status,
                category_id=cat_id if cat_id else None,
            )
            if tag_ids:
                post.tags.set(tag_ids)
            if 'cover_image' in request.FILES:
                post.cover_image = request.FILES['cover_image']
                post.save()
            messages.success(request, f'Post "{title}" created!')
            return redirect('dashboard_blogs')
        else:
            messages.error(request, 'Title and content are required.')

    return render(request, 'dashboard/blog_form.html', {
        'role': role, 'categories': categories, 'tags': tags, 'action': 'Create',
    })


@member_required
def dashboard_blog_edit(request, pk):
    role = get_member_role(request.user)
    if not role.can_manage_blog:
        return redirect('dashboard_home')

    post = get_object_or_404(Post, pk=pk)
    # non-admins can only edit their own
    if not role.is_admin and post.author != request.user:
        messages.error(request, 'You can only edit your own posts.')
        return redirect('dashboard_blogs')

    categories = Category.objects.all()
    tags       = Tag.objects.all()

    if request.method == 'POST':
        post.title   = request.POST.get('title', post.title).strip()
        post.content = request.POST.get('content', post.content).strip()
        post.excerpt = request.POST.get('excerpt', '').strip()
        cat_id       = request.POST.get('category')
        tag_ids      = request.POST.getlist('tags')
        status       = request.POST.get('status', 'draft')

        if not role.is_admin and status == 'published' and post.status != 'published':
            status = 'draft'
            messages.info(request, 'Only admins can publish. Saved as draft.')

        post.status      = status
        post.category_id = cat_id if cat_id else None
        if 'cover_image' in request.FILES:
            post.cover_image = request.FILES['cover_image']
        post.save()
        if tag_ids:
            post.tags.set(tag_ids)
        messages.success(request, 'Post updated!')
        return redirect('dashboard_blogs')

    return render(request, 'dashboard/blog_form.html', {
        'role': role, 'post': post,
        'categories': categories, 'tags': tags, 'action': 'Edit',
    })


@member_required
def dashboard_blog_delete(request, pk):
    role = get_member_role(request.user)
    if not role.can_delete:
        messages.error(request, 'Only admins can delete posts.')
        return redirect('dashboard_blogs')
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    messages.success(request, 'Post deleted.')
    return redirect('dashboard_blogs')


# ─────────────────────────────────────────────
#  EVENT MANAGEMENT
# ─────────────────────────────────────────────

@member_required
def dashboard_events(request):
    role = get_member_role(request.user)
    if not role.can_manage_events:
        messages.error(request, 'No event access.')
        return redirect('dashboard_home')

    events = Event.objects.all()
    if not role.is_admin:
        events = events.filter(organizer=request.user)

    q = request.GET.get('q', '')
    if q: events = events.filter(Q(title__icontains=q))
    events = events.order_by('-start_dt')

    return render(request, 'dashboard/events.html', {
        'role': role, 'events': events, 'q': q,
    })


@member_required
def dashboard_event_create(request):
    role = get_member_role(request.user)
    if not role.can_manage_events:
        return redirect('dashboard_home')

    categories = Category.objects.all()
    tags       = Tag.objects.all()

    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        venue       = request.POST.get('venue', '').strip()
        meet_link   = request.POST.get('meet_link', '').strip()
        mode        = request.POST.get('mode', 'offline')
        start_dt    = request.POST.get('start_dt')
        end_dt      = request.POST.get('end_dt')
        max_rsvp    = request.POST.get('max_rsvp', 0) or 0
        is_published= request.POST.get('is_published') == 'on'
        cat_id      = request.POST.get('category')
        tag_ids     = request.POST.getlist('tags')

        if not role.is_admin:
            is_published = False

        if title and start_dt and end_dt:
            event = Event.objects.create(
                title=title, description=description, venue=venue,
                meet_link=meet_link, mode=mode, start_dt=start_dt,
                end_dt=end_dt, max_rsvp=max_rsvp,
                is_published=is_published, organizer=request.user,
                category_id=cat_id if cat_id else None,
            )
            if tag_ids: event.tags.set(tag_ids)
            if 'cover_image' in request.FILES:
                event.cover_image = request.FILES['cover_image']
                event.save()
            messages.success(request, f'Event "{title}" created!')
            return redirect('dashboard_events')
        else:
            messages.error(request, 'Title, start and end date are required.')

    return render(request, 'dashboard/event_form.html', {
        'role': role, 'categories': categories, 'tags': tags, 'action': 'Create',
    })


@member_required
def dashboard_event_edit(request, pk):
    role  = get_member_role(request.user)
    if not role.can_manage_events:
        return redirect('dashboard_home')

    event = get_object_or_404(Event, pk=pk)
    if not role.is_admin and event.organizer != request.user:
        messages.error(request, 'You can only edit your own events.')
        return redirect('dashboard_events')

    categories = Category.objects.all()
    tags       = Tag.objects.all()

    if request.method == 'POST':
        event.title       = request.POST.get('title', event.title).strip()
        event.description = request.POST.get('description', '').strip()
        event.venue       = request.POST.get('venue', '').strip()
        event.meet_link   = request.POST.get('meet_link', '').strip()
        event.mode        = request.POST.get('mode', 'offline')
        event.start_dt    = request.POST.get('start_dt', event.start_dt)
        event.end_dt      = request.POST.get('end_dt', event.end_dt)
        event.max_rsvp    = request.POST.get('max_rsvp', 0) or 0
        cat_id            = request.POST.get('category')
        tag_ids           = request.POST.getlist('tags')
        if role.is_admin:
            event.is_published = request.POST.get('is_published') == 'on'
        event.category_id = cat_id if cat_id else None
        if 'cover_image' in request.FILES:
            event.cover_image = request.FILES['cover_image']
        event.save()
        if tag_ids: event.tags.set(tag_ids)
        messages.success(request, 'Event updated!')
        return redirect('dashboard_events')

    return render(request, 'dashboard/event_form.html', {
        'role': role, 'event': event,
        'categories': categories, 'tags': tags, 'action': 'Edit',
    })


@member_required
def dashboard_event_delete(request, pk):
    role = get_member_role(request.user)
    if not role.can_delete:
        messages.error(request, 'Only admins can delete events.')
        return redirect('dashboard_events')
    event = get_object_or_404(Event, pk=pk)
    event.delete()
    messages.success(request, 'Event deleted.')
    return redirect('dashboard_events')


# ─────────────────────────────────────────────
#  TEAM MANAGEMENT
# ─────────────────────────────────────────────

@member_required
def dashboard_team(request):
    role = get_member_role(request.user)
    if not role.can_manage_team:
        messages.error(request, 'No team access.')
        return redirect('dashboard_home')

    members    = TeamMember.objects.select_related('team').order_by('team__order', 'order')
    categories = TeamCategory.objects.all()
    return render(request, 'dashboard/team.html', {
        'role': role, 'members': members, 'categories': categories,
    })


@member_required
def dashboard_team_toggle(request, pk):
    """Quick toggle active/inactive for a team member."""
    role = get_member_role(request.user)
    if not role.can_manage_team:
        return redirect('dashboard_home')
    member = get_object_or_404(TeamMember, pk=pk)
    member.is_active = not member.is_active
    member.save()
    messages.success(request, f'{"Activated" if member.is_active else "Deactivated"} {member.name}.')
    return redirect('dashboard_team')


# ─────────────────────────────────────────────
#  COMMENTS MODERATION
# ─────────────────────────────────────────────

@member_required
def dashboard_comments(request):
    role = get_member_role(request.user)
    if not role.can_manage_blog:
        return redirect('dashboard_home')

    comments = Comment.objects.select_related('post', 'author').order_by('-created_at')
    return render(request, 'dashboard/comments.html', {
        'role': role, 'comments': comments,
    })


@member_required
def dashboard_comment_toggle(request, pk):
    role = get_member_role(request.user)
    if not role.can_manage_blog:
        return redirect('dashboard_home')
    comment = get_object_or_404(Comment, pk=pk)
    comment.is_active = not comment.is_active
    comment.save()
    messages.success(request, f'Comment {"approved" if comment.is_active else "hidden"}.')
    return redirect('dashboard_comments')


@member_required
def dashboard_team_create(request):
    role = get_member_role(request.user)
    if not role.can_manage_team:
        messages.error(request, 'No team access.')
        return redirect('dashboard_home')

    categories = TeamCategory.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        role_title = request.POST.get('role', '').strip()
        team_id = request.POST.get('team')
        branch = request.POST.get('branch', '').strip()
        year = request.POST.get('year', '').strip()
        bio = request.POST.get('bio', '').strip()
        skills = request.POST.get('skills', '').strip()
        github = request.POST.get('github', '').strip()
        linkedin = request.POST.get('linkedin', '').strip()
        twitter = request.POST.get('twitter', '').strip()
        instagram = request.POST.get('instagram', '').strip()
        gfg_profile = request.POST.get('gfg_profile', '').strip()
        leetcode = request.POST.get('leetcode', '').strip()
        email = request.POST.get('email', '').strip()
        portfolio = request.POST.get('portfolio', '').strip()
        order = request.POST.get('order', 0) or 0
        is_active = request.POST.get('is_active') == 'on'

        if name and role_title and team_id:
            member = TeamMember.objects.create(
                name=name, role=role_title, branch=branch, year=year,
                bio=bio, skills=skills, github=github, linkedin=linkedin,
                twitter=twitter, instagram=instagram, gfg_profile=gfg_profile,
                leetcode=leetcode, email=email, portfolio=portfolio,
                order=order, is_active=is_active,
                team_id=team_id,
            )
            if 'photo' in request.FILES:
                member.photo = request.FILES['photo']
                member.save()
            messages.success(request, f'Team member "{name}" created!')
            return redirect('dashboard_team')
        else:
            messages.error(request, 'Name, Role and Team are required.')

    return render(request, 'dashboard/team_form.html', {
        'role': role, 'categories': categories, 'action': 'Create', 'member': None,
    })


@member_required
def dashboard_team_edit(request, pk):
    role = get_member_role(request.user)
    if not role.can_manage_team:
        messages.error(request, 'No team access.')
        return redirect('dashboard_home')

    member = get_object_or_404(TeamMember, pk=pk)
    categories = TeamCategory.objects.all()

    if request.method == 'POST':
        member.name = request.POST.get('name', member.name).strip()
        member.role = request.POST.get('role', member.role).strip()
        member.branch = request.POST.get('branch', '').strip()
        member.year = request.POST.get('year', '').strip()
        member.bio = request.POST.get('bio', '').strip()
        member.skills = request.POST.get('skills', '').strip()
        member.github = request.POST.get('github', '').strip()
        member.linkedin = request.POST.get('linkedin', '').strip()
        member.twitter = request.POST.get('twitter', '').strip()
        member.instagram = request.POST.get('instagram', '').strip()
        member.gfg_profile = request.POST.get('gfg_profile', '').strip()
        member.leetcode = request.POST.get('leetcode', '').strip()
        member.email = request.POST.get('email', '').strip()
        member.portfolio = request.POST.get('portfolio', '').strip()
        member.order = request.POST.get('order', 0) or 0
        member.is_active = request.POST.get('is_active') == 'on'
        team_id = request.POST.get('team')
        if team_id:
            member.team_id = team_id
        if 'photo' in request.FILES:
            member.photo = request.FILES['photo']
        member.save()
        messages.success(request, f'"{member.name}" updated!')
        return redirect('dashboard_team')

    return render(request, 'dashboard/team_form.html', {
        'role': role, 'categories': categories,
        'action': 'Edit', 'member': member,
    })


@member_required
def dashboard_team_delete(request, pk):
    role = get_member_role(request.user)
    if not role.can_delete:
        messages.error(request, 'Only admins can delete team members.')
        return redirect('dashboard_team')
    member = get_object_or_404(TeamMember, pk=pk)
    name = member.name
    member.delete()
    messages.success(request, f'"{name}" deleted.')
    return redirect('dashboard_team')


@member_required
def dashboard_about(request):
    """Overview of about page sections."""
    role = get_member_role(request.user)
    if not role.is_admin:
        messages.error(request, 'Only Admins can manage the About page.')
        return redirect('dashboard_home')

    about = AboutPage.get()
    achievements = Achievement.objects.all().order_by('order', '-date')
    values = ValueCard.objects.all().order_by('order')
    faqs = FAQ.objects.all().order_by('order')
    contacts = ContactMessage.objects.all().order_by('-submitted_at')[:10]

    return render(request, 'dashboard/about.html', {
        'role': role,
        'about': about,
        'achievements': achievements,
        'values': values,
        'faqs': faqs,
        'contacts': contacts,
        'total_contacts': ContactMessage.objects.count(),
        'unread_contacts': ContactMessage.objects.filter(is_read=False).count(),
    })


@member_required
def dashboard_about_edit(request):
    """Edit the main About page content."""
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')

    about = AboutPage.get()

    if request.method == 'POST':
        about.hero_tagline = request.POST.get('hero_tagline', '').strip()
        about.hero_heading = request.POST.get('hero_heading', '').strip()
        about.hero_subtext = request.POST.get('hero_subtext', '').strip()
        about.story_heading = request.POST.get('story_heading', '').strip()
        about.story_body = request.POST.get('story_body', '').strip()
        about.vision_heading = request.POST.get('vision_heading', '').strip()
        about.vision_text = request.POST.get('vision_text', '').strip()
        about.mission_text = request.POST.get('mission_text', '').strip()
        about.contact_email = request.POST.get('contact_email', '').strip()
        about.contact_phone = request.POST.get('contact_phone', '').strip()
        about.contact_address = request.POST.get('contact_address', '').strip()
        about.contact_map_url = request.POST.get('contact_map_url', '').strip()
        about.social_instagram = request.POST.get('social_instagram', '').strip()
        about.social_linkedin = request.POST.get('social_linkedin', '').strip()
        about.social_twitter = request.POST.get('social_twitter', '').strip()
        about.social_github = request.POST.get('social_github', '').strip()
        about.social_youtube = request.POST.get('social_youtube', '').strip()
        about.social_discord = request.POST.get('social_discord', '').strip()
        about.save()
        messages.success(request, 'About page updated successfully!')
        return redirect('dashboard_about')

    return render(request, 'dashboard/about_edit.html', {
        'role': role, 'about': about,
    })


# ── ACHIEVEMENTS ─────────────────────────────

@member_required
def dashboard_achievement_create(request):
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '🏆')
        highlight = request.POST.get('highlight', '').strip()
        date = request.POST.get('date') or None
        order = request.POST.get('order', 0) or 0

        if title:
            Achievement.objects.create(
                title=title, description=description, icon=icon,
                highlight=highlight, date=date, order=order, is_active=True,
            )
            messages.success(request, f'Achievement "{title}" added!')
            return redirect('dashboard_about')
        else:
            messages.error(request, 'Title is required.')

    return render(request, 'dashboard/about_edit.html', {
        'role': role, 'action': 'Add',
    })


@member_required
def dashboard_achievement_edit(request, pk):
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')

    obj = get_object_or_404(Achievement, pk=pk)

    if request.method == 'POST':
        obj.title = request.POST.get('title', '').strip()
        obj.description = request.POST.get('description', '').strip()
        obj.icon = request.POST.get('icon', '🏆')
        obj.highlight = request.POST.get('highlight', '').strip()
        obj.date = request.POST.get('date') or None
        obj.order = request.POST.get('order', 0) or 0
        obj.is_active = request.POST.get('is_active') == 'on'
        obj.save()
        messages.success(request, 'Achievement updated!')
        return redirect('dashboard_about')

    return render(request, 'dashboard/about_edit.html', {
        'role': role, 'obj': obj, 'action': 'Edit',
    })


@member_required
def dashboard_achievement_delete(request, pk):
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')
    get_object_or_404(Achievement, pk=pk).delete()
    messages.success(request, 'Achievement deleted.')
    return redirect('dashboard_about')

# ─────────────────────────────────────────────
# Add to app1/views.py
# Also add EventPhoto to your model imports
# ─────────────────────────────────────────────

from .models import EventPhoto   # add to existing import line

@member_required
def dashboard_event_photos(request, pk):
    """Manage photos for a specific event."""
    role  = get_member_role(request.user)
    if not role.can_manage_events:
        return redirect('dashboard_home')

    event = get_object_or_404(Event, pk=pk)

    # only admin or event organiser can manage photos
    if not role.is_admin and event.organizer != request.user:
        messages.error(request, 'You can only manage photos for your own events.')
        return redirect('dashboard_events')

    if request.method == 'POST':
        images  = request.FILES.getlist('photos')
        caption = request.POST.get('caption', '').strip()
        if images:
            for i, img in enumerate(images):
                last_order = EventPhoto.objects.filter(event=event).count()
                EventPhoto.objects.create(
                    event   = event,
                    image   = img,
                    caption = caption,
                    order   = last_order + i,
                )
            messages.success(request, f'{len(images)} photo(s) uploaded successfully!')
        else:
            messages.error(request, 'Please select at least one photo.')
        return redirect('dashboard_event_photos', pk=pk)

    photos = event.photos.all()
    return render(request, 'dashboard/event_photos.html', {
        'role':   role,
        'event':  event,
        'photos': photos,
    })


@member_required
def dashboard_event_photo_delete(request, pk, photo_pk):
    """Delete a single event photo."""
    role = get_member_role(request.user)
    if not role.can_manage_events:
        return redirect('dashboard_home')
    photo = get_object_or_404(EventPhoto, pk=photo_pk, event__pk=pk)
    photo.image.delete(save=False)   # delete actual file
    photo.delete()
    messages.success(request, 'Photo deleted.')
    return redirect('dashboard_event_photos', pk=pk)
# ── VALUES ───────────────────────────────────

@member_required
def dashboard_value_create(request):
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '💡')
        order = request.POST.get('order', 0) or 0

        if title and description:
            ValueCard.objects.create(
                title=title, description=description, icon=icon,
                order=order, is_active=True,
            )
            messages.success(request, f'Value "{title}" added!')
            return redirect('dashboard_about')
        else:
            messages.error(request, 'Title and description are required.')

    return render(request, 'dashboard/value_form.html', {
        'role': role, 'action': 'Add',
    })


@member_required
def dashboard_value_edit(request, pk):
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')

    obj = get_object_or_404(ValueCard, pk=pk)

    if request.method == 'POST':
        obj.title = request.POST.get('title', '').strip()
        obj.description = request.POST.get('description', '').strip()
        obj.icon = request.POST.get('icon', '💡')
        obj.order = request.POST.get('order', 0) or 0
        obj.is_active = request.POST.get('is_active') == 'on'
        obj.save()
        messages.success(request, 'Value updated!')
        return redirect('dashboard_about')

    return render(request, 'dashboard/value_form.html', {
        'role': role, 'obj': obj, 'action': 'Edit',
    })


@member_required
def dashboard_value_delete(request, pk):
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')
    get_object_or_404(ValueCard, pk=pk).delete()
    messages.success(request, 'Value deleted.')
    return redirect('dashboard_about')


# ── FAQs ─────────────────────────────────────

@member_required
def dashboard_faq_create(request):
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')

    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        answer = request.POST.get('answer', '').strip()
        order = request.POST.get('order', 0) or 0

        if question and answer:
            FAQ.objects.create(question=question, answer=answer, order=order, is_active=True)
            messages.success(request, 'FAQ added!')
            return redirect('dashboard_about')
        else:
            messages.error(request, 'Question and answer are required.')

    return render(request, 'dashboard/faq_form.html', {
        'role': role, 'action': 'Add',
    })


@member_required
def dashboard_faq_edit(request, pk):
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')

    obj = get_object_or_404(FAQ, pk=pk)

    if request.method == 'POST':
        obj.question = request.POST.get('question', '').strip()
        obj.answer = request.POST.get('answer', '').strip()
        obj.order = request.POST.get('order', 0) or 0
        obj.is_active = request.POST.get('is_active') == 'on'
        obj.save()
        messages.success(request, 'FAQ updated!')
        return redirect('dashboard_about')

    return render(request, 'dashboard/faq_form.html', {
        'role': role, 'obj': obj, 'action': 'Edit',
    })


@member_required
def dashboard_faq_delete(request, pk):
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')
    get_object_or_404(FAQ, pk=pk).delete()
    messages.success(request, 'FAQ deleted.')
    return redirect('dashboard_about')


# ── CONTACT MESSAGES ─────────────────────────

@member_required
def dashboard_contacts(request):
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')

    contacts = ContactMessage.objects.all().order_by('-submitted_at')
    return render(request, 'dashboard/contacts.html', {
        'role': role, 'contacts': contacts,
    })


@member_required
def dashboard_contact_read(request, pk):
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.is_read = True
    msg.save()
    return redirect('dashboard_contacts')


@member_required
def dashboard_contact_delete(request, pk):
    role = get_member_role(request.user)
    if not role.is_admin:
        return redirect('dashboard_home')
    get_object_or_404(ContactMessage, pk=pk).delete()
    messages.success(request, 'Message deleted.')
    return redirect('dashboard_contacts')