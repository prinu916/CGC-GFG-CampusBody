# CGC-GFG Campus Body Website

A Django-powered website for managing and showcasing the CGC GFG Campus Body activities, teams, events, blog, and dashboard.

## Features
- Public pages: Home, About, Team, Events, Blog, Search
- Admin Dashboard: Manage teams/categories/members, events/photos, blog posts, contacts, FAQ, achievements, value cards
- Contact form
- Responsive templates

## Local Development Setup
1. Clone the repository:
   ```
   git clone https://github.com/prinu916/CGC-GFG-CampusBody.git
   cd CGC-GFG-CampusBody
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Apply migrations:
   ```
   python manage.py migrate
   ```
4. Create superuser:
   ```
   python manage.py createsuperuser
   ```
5. Run development server:
   ```
   python manage.py runserver
   ```
   Open http://127.0.0.1:8000/

## Production Deployment (e.g., Heroku/Railway/PythonAnywhere)
1. Use PostgreSQL DB (update DATABASES in settings.py).
2. Set environment variables:
   - `SECRET_KEY`: Generate new secure key
   - `DEBUG`: False
   - `ALLOWED_HOSTS`: Your domain/IPs
3. Install gunicorn: Add `gunicorn` to requirements.
4. Procfile: `web: gunicorn gfg.wsgi --log-file -`
5. Collect static: `python manage.py collectstatic`
6. Push to platform.

## Admin Login
Use /dashboard/login/ with superuser credentials.

## File Structure
- `gfg/`: Project settings
- `app1/`: Main app with models/views/templates
- `team/photos/`, `events/covers/`: Media (update MEDIA_URL/MEDIA_ROOT in settings for prod)

Built with Django 6.0.1.
