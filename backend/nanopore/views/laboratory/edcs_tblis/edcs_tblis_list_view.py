from django.db.models import Max, Min
from django.views.generic import ListView

from nanopore.edcs_tblis_cards import CARDS, DEFAULT_CARD, SECTIONS, card_queryset, latest_batch
from nanopore.models import EdcsTblisMergeSummary, EdcsTblisZonal
from nanopore.substudy import SUBSTUDIES
from utils import access
from utils.access import is_unscoped
from utils.access_mixins import FormAccessMixin
from utils.roles import get_role_context


class EdcsTBLISLaboratoryListView(FormAccessMixin, ListView):
    """EDCS / TB-LIS records: summary cards (nanopore/edcs_tblis_cards.py) and the list behind the chosen card."""
    access_form = access.EDCS_TBLIS
    model = EdcsTblisZonal
    template_name = "nanopore/laboratory/edcs_tblis/edcs_tblis_laboratory_list.html"
    context_object_name = "object_list"
    paginate_by = 30

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.batch = latest_batch()
        card = request.GET.get("card_type") or request.GET.get("view_type")
        self.card = CARDS.get(card) or CARDS[DEFAULT_CARD]

    def card_records(self, key):
        """A card's records within the user's sites. Raw TB-LIS rows have no site: unscoped users only."""
        qs = card_queryset(key, self.batch)
        if CARDS[key].source == "tblis":
            return qs if is_unscoped(self.request.user) else qs.none()
        return self.scope(qs)

    def get_queryset(self):
        qs = self.card_records(self.card.key)
        params = self.request.GET
        if self.card.source == "tblis":
            if params.get("unique_lab_no"):
                qs = qs.filter(labno__icontains=params["unique_lab_no"])
            return qs
        if params.get("zone"):
            qs = qs.filter(screening__site__district__region__zone_id=params["zone"])
        if params.get("site"):
            qs = qs.filter(screening__site_id=params["site"])
        if params.get("pid"):
            qs = qs.filter(screening__pid__icontains=params["pid"])
        if params.get("unique_lab_no"):
            qs = qs.filter(unique_lab_no__icontains=params["unique_lab_no"])
        if params.get("substudy") in SUBSTUDIES:
            qs = qs.filter(substudy_group=params["substudy"])
        if params.get("start_date"):
            qs = qs.filter(date_sputum_received__gte=params["start_date"])
        if params.get("end_date"):
            qs = qs.filter(date_sputum_received__lte=params["end_date"])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_role_context(self.request.user))
        unscoped = is_unscoped(self.request.user)

        counts = {
            key: self.card_records(key).count()
            for key, card in CARDS.items()
            if card.source != "tblis" or unscoped
        }
        sections = []
        for title, note, cards in SECTIONS:
            items = []
            for card in cards:
                if card.key not in counts:
                    continue
                total = counts.get(card.share_of)
                items.append({
                    "card": card,
                    "count": counts[card.key],
                    "share": round(counts[card.key] / total * 100, 1) if card.share_of and total else None,
                })
            if items:
                sections.append({"title": title, "note": note, "cards": items})

        merge_summary = (
            EdcsTblisMergeSummary.objects.filter(upload_batch=self.batch).first()
            if self.batch else EdcsTblisMergeSummary.objects.first()
        )
        ctrl, merged = counts["ctrl"], counts["merged"]
        dates = self.scope(EdcsTblisZonal.objects.all()).aggregate(
            date_from=Min("date_sputum_received"), date_to=Max("date_sputum_received"),
        )

        params = self.request.GET.copy()
        params.pop("page", None)
        filters = params.copy()
        filters.pop("card_type", None)
        filters.pop("view_type", None)
        context.update({
            "sections": sections,
            "active_card": self.card,
            "is_tblis_list": self.card.source == "tblis",
            "coverage": round(merged / ctrl * 100, 1) if ctrl else 0,
            "merged_count": merged,
            "ctrl_count": ctrl,
            "latest_upload_batch": self.batch,
            "merge_summary": merge_summary,
            "edcs_date_from": dates["date_from"],
            "edcs_date_to": dates["date_to"],
            "query_params": params.urlencode(),       # pagination keeps card + filters
            "filter_params": filters.urlencode(),      # card links keep the filters
            "substudies": SUBSTUDIES,
            "has_filters": any(filters.get(k) for k in ("zone", "site", "pid", "unique_lab_no", "substudy", "start_date", "end_date")),
        })
        return context
