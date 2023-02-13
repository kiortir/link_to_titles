"""
initialize db
"""

from yoyo import step

__depends__ = {}  # type: ignore

steps = [
    step(
        """
    CREATE TABLE processed_link (
        id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
        url TEXT NOT NULL UNIQUE
    );
    """
    ),
    step(
        """
    CREATE TABLE image (
        id uuid PRIMARY KEY NOT NULL DEFAULT gen_random_uuid(),
        ext TEXT NOT NULL,
        link_id int NOT NULL,
        CONSTRAINT fk_processed_link FOREIGN KEY(link_id) REFERENCES processed_link(id)
    );
    """
    ),
    step(
        """
    CREATE TABLE session (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid()
    );
    """
    ),
    step(
        """
    CREATE TABLE session_link (
        session_id uuid REFERENCES session(id) ON UPDATE CASCADE ON DELETE CASCADE,
        processed_link_id int REFERENCES processed_link(id) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT session_link_pkey PRIMARY KEY (session_id, processed_link_id)
    );
    """
    ),
]