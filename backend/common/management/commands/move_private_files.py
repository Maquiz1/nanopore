import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

# Old public locations -> new private location
MOVES = [
    (Path(settings.MEDIA_ROOT) / "exports", Path(settings.PRIVATE_EXPORTS_DIR)),
    (Path(settings.MEDIA_ROOT) / "imports", Path(settings.PRIVATE_IMPORTS_DIR) / "legacy_uploads"),
    (Path(settings.BASE_DIR) / "media" / "imports", Path(settings.PRIVATE_IMPORTS_DIR) / "legacy_media"),
]


class Command(BaseCommand):
    help = "Move export files and uploaded source files out of the public media folders into PRIVATE_ROOT"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only list what would be moved")

    def handle(self, *args, **options):
        moved = 0
        for source, target in MOVES:
            if not source.exists():
                continue
            for path in sorted(p for p in source.rglob("*") if p.is_file()):
                destination = target / path.relative_to(source)
                if destination.exists():
                    self.stdout.write(self.style.WARNING(f"Skipped (already exists): {destination}"))
                    continue
                self.stdout.write(f"{'Would move' if options['dry_run'] else 'Moving'} {path} -> {destination}")
                if not options["dry_run"]:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(path), str(destination))
                moved += 1
        verb = "would be moved" if options["dry_run"] else "moved"
        self.stdout.write(self.style.SUCCESS(f"✅ {moved} file(s) {verb} to {settings.PRIVATE_ROOT}."))
