"""
Move Substudy 4 participants' Zonal Lab forms (with their EDCS/TBLIS records) to the Recycle Bin.

    python manage.py set_aside_substudy4_zonal                       # preview: counts only, nothing changes
    python manage.py set_aside_substudy4_zonal --list                # preview with the PIDs
    python manage.py set_aside_substudy4_zonal --apply --user NAME   # do it, recorded as NAME

One Recycle Bin entry per participant, reason "Substudy 4: not entered in Zonal Lab",
so an admin can restore any of them later (nanopore/substudy4_set_aside.py).
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from nanopore import recycle_bin
from nanopore.models import EdcsTblisZonal
from nanopore.substudy4_set_aside import SET_ASIDE_REASON, substudy4_zonal_labs
from nanopore.zonal_rules import LAB_NUMBER_ONLY_Q


class Command(BaseCommand):
    help = "Set aside Substudy 4 participants' Zonal Lab forms in the Recycle Bin (preview unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Move them to the Recycle Bin (default: preview only).")
        parser.add_argument("--user", help="Username recorded as having deleted them (required with --apply).")
        parser.add_argument("--list", action="store_true", help="Also print the PIDs.")

    def handle(self, *args, **options):
        labs = substudy4_zonal_labs().select_related("screening").order_by("screening__pid")
        edcs = EdcsTblisZonal.objects.filter(screening__in=labs.values("screening"))
        has_results = Q(lj_results__isnull=False) | Q(mgit_results__isnull=False)
        self.stdout.write(f"Substudy 4 Zonal Lab forms: {labs.count()} "
                          f"(Dar es Salaam {labs.filter(LAB_NUMBER_ONLY_Q).count()}, other zones {labs.exclude(LAB_NUMBER_ONLY_Q).count()})")
        self.stdout.write(f"Their EDCS/TBLIS records: {edcs.count()}; with a culture result {edcs.filter(has_results).count()}, "
                          f"phenotypic DST {edcs.filter(phenotypic_performed=1).count()}, Nanopore done {edcs.filter(nanopore_done=1).count()}")
        if options["list"]:
            for lab in labs:
                self.stdout.write(f"  {lab.screening.pid}  lab no. {lab.unique_lab_no}")

        if not options["apply"]:
            self.stdout.write("Preview only: nothing changed. Run again with --apply --user <username> to move them to the Recycle Bin.")
            return
        if not options["user"]:
            raise CommandError("--apply needs --user <username>: the Recycle Bin records who set them aside.")
        try:
            user = get_user_model().objects.get(username=options["user"])
        except get_user_model().DoesNotExist:
            raise CommandError(f"No user called {options['user']!r}.")

        moved = 0
        for lab in list(labs):
            recycle_bin.soft_delete(lab, user, reason=SET_ASIDE_REASON)
            moved += 1
        self.stdout.write(self.style.SUCCESS(
            f"Moved {moved} Zonal Lab forms (and their EDCS/TBLIS records) to the Recycle Bin, "
            f"reason \"{SET_ASIDE_REASON}\". Restore any of them from Forms > Recycle Bin."))
