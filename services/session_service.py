from repository import session_repo
from datetime import datetime

class SessionService:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.session_id = None

    def start_session(self):
        """Start a new session."""
        self.session_id = session_repo.create_session(self.user_id)
        return self.session_id

    def end_session(self):
        """End the current session."""
        if self.session_id:
            session_repo.end_session(self.session_id)
            self.session_id = None