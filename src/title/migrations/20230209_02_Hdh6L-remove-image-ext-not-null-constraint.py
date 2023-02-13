"""
remove image ext/link_id not_null constraint
"""

from yoyo import step

__depends__ = {'20230209_01_3xNPL'}

steps = [
    step("""
    ALTER TABLE image
        ALTER COLUMN ext DROP NOT NULL,
        ALTER COLUMN link_id DROP NOT NULL;
    """)
]
