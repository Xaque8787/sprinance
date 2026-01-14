import re
from sqlalchemy.orm import Session

def create_slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = text.strip('-')
    return text

def create_field_name(text: str) -> str:
    """Convert text to snake_case field name"""
    slug = create_slug(text)
    return slug.replace('-', '_')

def ensure_unique_slug(db: Session, model, base_slug: str, exclude_id: int = None, field: str = 'slug') -> str:
    slug = base_slug
    counter = 1

    while True:
        field_attr = getattr(model, field)
        query = db.query(model).filter(field_attr == slug)
        if exclude_id:
            query = query.filter(model.id != exclude_id)

        if not query.first():
            return slug

        slug = f"{base_slug}-{counter}"
        counter += 1
