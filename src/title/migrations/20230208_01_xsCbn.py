"""

"""

from yoyo import step

__depends__ = {'20230206_01_kRWXE'}

steps = [
    step("""
    ALTER TABLE processed_link
        ADD COLUMN title TEXT,
        ADD COLUMN status TEXT DEFAULT 'PENDING'    
    """)
]
