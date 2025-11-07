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