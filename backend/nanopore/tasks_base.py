from celery import Task

class RevocableTask(Task):
    def is_revoked(self):
        """Check if task was revoked"""
        return getattr(self.request, "revoke", False)