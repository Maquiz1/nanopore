from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from users.models import Profile


class Command(BaseCommand):
    help = "Add users whose Profile position is 'Data Specialist' to the DATA_SPECIALIST group"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only list the users that would be added")

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name="DATA_SPECIALIST")
        profiles = Profile.objects.filter(position__name__iexact="data specialist").select_related("user")

        added = 0
        for profile in profiles:
            user = profile.user
            if user.groups.filter(pk=group.pk).exists():
                continue
            self.stdout.write(f"{'Would add' if options['dry_run'] else 'Adding'} {user.username}")
            if not options["dry_run"]:
                user.groups.add(group)
            added += 1

        self.stdout.write(self.style.SUCCESS(f"✅ {added} user(s) {'to add' if options['dry_run'] else 'added'} to DATA_SPECIALIST."))
