def log_product_visit(product_id):
    # Function to log product visits
    pass

def authenticate_user(username, password):
    # Function to authenticate admin users
    pass

def calculate_cart_total(cart_items):
    # Function to calculate the total price of items in the cart
    pass

def validate_trxID(trxID):
    # Function to validate the Bkash transaction ID
    pass


def generate_slug(title, model_class=None, existing_id=None):
    """Generate a unique URL-safe slug from a title.
    
    Args:
        title: The title to convert to a slug
        model_class: The model class to check for uniqueness (e.g., BlogPost)
        existing_id: ID of existing record (for updates, to exclude from uniqueness check)
    
    Returns:
        A unique, URL-safe slug
    """
    import re
    import unicodedata
    
    # Convert to lowercase and normalize unicode
    slug = unicodedata.normalize('NFKD', title.lower())
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    
    # Replace spaces and special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    
    # Limit length
    slug = slug[:200]
    
    # If no model class provided, just return the slug
    if not model_class:
        return slug
    
    # Check for uniqueness
    original_slug = slug
    counter = 1
    
    while True:
        # Query to check if slug exists
        query = model_class.query.filter_by(slug=slug)
        
        # Exclude current record if updating
        if existing_id:
            query = query.filter(model_class.id != existing_id)
        
        if not query.first():
            break
        
        # Slug exists, add counter
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    return slug


def render_markdown_safe(text):
    """Render Markdown to HTML and sanitize it with bleach.

    Returns a tuple (html, toc_html).
    """
    try:
        import markdown
        import bleach
    except Exception:
        # If libraries are missing, return escaped text
        return ("<pre>" + (text or '') + "</pre>", "")

    # create markdown renderer with TOC and fenced code support
    md = markdown.Markdown(extensions=["fenced_code", "tables", "toc"])
    raw_html = md.convert(text or "")
    toc_html = getattr(md, 'toc', '') or ''

    # Allow common tags produced by markdown
    # build allowed tags/attributes for bleach
    allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS) | {
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'pre', 'code', 'img', 'blockquote',
        'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'ul', 'ol', 'li', 'br'
    }

    allowed_attrs = {
        '*': ['class', 'id'],
        'a': ['href', 'title', 'rel', 'target'],
        'img': ['src', 'alt', 'title', 'loading', 'class'],
        'th': ['colspan', 'rowspan'],
        'td': ['colspan', 'rowspan']
    }

    cleaned = bleach.clean(raw_html, tags=allowed_tags, attributes=allowed_attrs, strip=True)

    # linkify (turn plain URLs into <a>) and ensure target/rel for external links
    def set_target(attrs, new=False):
        href = attrs.get('href', '')
        if href and href.startswith('http'):
            attrs['target'] = '_blank'
            attrs['rel'] = 'noopener noreferrer'
        return attrs

    linked = bleach.linkify(cleaned, callbacks=[set_target])

    # Add lazy loading and responsive class to img tags by post-processing a bit
    # (simple transform: add loading="lazy" and class="max-w-full h-auto")
    import re
    def _img_repl(m):
        tag = m.group(0)
        if 'loading=' not in tag:
            tag = tag.replace('<img', '<img loading="lazy"')
        if 'class=' not in tag:
            tag = tag.replace('<img', '<img class="max-w-full h-auto"')
        return tag

    final = re.sub(r'<img[^>]*>', _img_repl, linked)

    return (final, toc_html)


def safe_admin_flash(full_message, display=None, level='info'):
    """Log a detailed admin-only message to the server log and flash a safe
    (optionally custom) display message with category 'admin'. This prevents
    sensitive details (paths, ids) from leaking to non-admin UI views.

    - full_message: full detail to write to server logs
    - display: short/safe string to flash to admins (optional). If omitted,
      a generic message 'Action completed' will be flashed.
    - level: logging level (info, warning, error)
    """
    try:
        from flask import flash, current_app
    except Exception:
        # not running in app context; fallback to printing
        try:
            print('ADMIN:', full_message)
        except Exception:
            pass
        return

    # log full detail for audit/debugging
    try:
        if level == 'warning':
            current_app.logger.warning(full_message)
        elif level == 'error':
            current_app.logger.error(full_message)
        else:
            current_app.logger.info(full_message)
    except Exception:
        # swallow logging errors
        pass

    # flash only admin-category message (visible only to admins in templates)
    try:
        safe = display if display is not None else 'Action completed.'
        flash(safe, category='admin')
    except Exception:
        # if flashing fails, at least we've logged it
        pass