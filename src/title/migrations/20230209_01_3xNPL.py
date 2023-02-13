"""

"""

from yoyo import step

__depends__ = {'20230208_01_xsCbn'}

steps = [
        step("""
    ALTER TABLE image
        ADD COLUMN status TEXT DEFAULT 'PENDING',
        ADD COLUMN origin TEXT
    """)
]
