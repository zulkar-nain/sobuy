"""
Script to add slug field to existing BlogPost records.
This should be run after the migration adds the slug column.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import BlogPost
from app.utils import generate_slug

def add_slugs_to_existing_posts():
    """Add slugs to all existing blog posts that don't have one."""
    app = create_app()
    with app.app_context():
        posts = BlogPost.query.all()
        updated = 0
        
        for post in posts:
            # Only update if slug is None or empty
            if not post.slug:
                try:
                    post.slug = generate_slug(post.title, BlogPost, existing_id=post.id)
                    print(f"Generated slug for post #{post.id}: '{post.title}' -> '{post.slug}'")
                    updated += 1
                except Exception as e:
                    print(f"Error generating slug for post #{post.id}: {e}")
        
        if updated > 0:
            try:
                db.session.commit()
                print(f"\nSuccessfully updated {updated} blog post(s) with slugs.")
            except Exception as e:
                db.session.rollback()
                print(f"Error committing changes: {e}")
        else:
            print("No blog posts needed slug updates.")

if __name__ == '__main__':
    add_slugs_to_existing_posts()
