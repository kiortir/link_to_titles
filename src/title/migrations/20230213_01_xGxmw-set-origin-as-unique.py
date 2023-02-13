"""
set_origin_as_unique_
"""

from yoyo import step

__depends__ = {'20230209_02_Hdh6L-remove-image-ext-not-null-constraint'}

steps = [
    step("""
    ALTER TABLE image
        ADD UNIQUE (origin);
    """)
]
