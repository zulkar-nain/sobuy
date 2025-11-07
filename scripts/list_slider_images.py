"""
List HomeSliderImage records for debugging.
Run:
    python scripts/list_slider_images.py
"""
import os
import sys

# Ensure project root is on sys.path when running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import HomeSliderImage


def main():
    app = create_app()
    with app.app_context():
        imgs = HomeSliderImage.query.order_by(HomeSliderImage.position.asc()).all()
        if not imgs:
            print('No slider images found')
        else:
            print(f'Found {len(imgs)} slider images:')
            for img in imgs:
                print(f' - id={img.id}, url={img.image_url}, position={img.position}, active={img.active}, created_at={img.created_at}')


if __name__ == '__main__':
    main()
