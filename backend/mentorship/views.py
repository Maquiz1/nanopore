from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView,CreateView,UpdateView, DeleteView
from django.contrib import messages
from django.shortcuts import redirect
from .models import Visit,VisitDay,AssignedCompetence
from .forms import VisitForm,VisitDayForm,AssignedCompetenceForm,MentorGradeForm,MenteeSelfAssessmentForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden


def index(request):
    return render(request, 'mentorship/index.html')


class VisitListView(ListView):
    model = Visit
    template_name = 'mentorship/visit_list.html'
    context_object_name = 'visits'
    ordering = ['-start_date']


class VisitDetailView(DetailView):
    model = Visit
    template_name = 'mentorship/visit_detail.html'
    context_object_name = 'visit'
    
class VisitCreateView(CreateView):
    model = Visit
    form_class = VisitForm
    template_name = 'mentorship/visit_form.html'

    def form_valid(self, form):
        messages.success(self.request, "Visit created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('visit_detail', kwargs={'pk': self.object.pk})


class VisitDeleteView(DeleteView):
    model = Visit
    template_name = 'mentorship/visit_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Visit deleted successfully.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('visit_list')
    

class VisitDayDetailView(LoginRequiredMixin, DetailView):
    model = VisitDay
    template_name = 'mentorship/visit_day_detail.html'
    context_object_name = 'visit_day'
    pk_url_kwarg = 'visit_day_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignments'] = self.object.assignments.all()
        return context
    
class VisitDayUpdateView(UpdateView):
    model = VisitDay
    form_class = VisitDayForm
    template_name = 'mentorship/edit_visit_day.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['visit'] = self.object.visit
        return kwargs

    def get_success_url(self):
        messages.success(self.request, "Visit Day updated successfully.")
        return reverse_lazy('visit_detail', kwargs={'pk': self.object.visit.pk})


class VisitDayDeleteView(DeleteView):
    model = VisitDay
    template_name = 'mentorship/delete_visit_day.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.assignments.exists():
            messages.error(request, "Cannot delete this Visit Day as it has assigned competencies.")
            return redirect('visit_detail', pk=obj.visit.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Visit Day deleted successfully.")
        return reverse_lazy('visit_detail', kwargs={'pk': self.object.visit.pk})
    
    
class AssignCompetenceView(LoginRequiredMixin, CreateView):
    model = AssignedCompetence
    form_class = AssignedCompetenceForm
    template_name = 'mentorship/assign_competence.html'

    def get_initial(self):
        initial = super().get_initial()
        visit_day_id = self.kwargs.get('visit_day_id')
        visit_day = VisitDay.objects.get(pk=visit_day_id)
        initial['visit_day'] = visit_day
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visit_day_id = self.kwargs.get('visit_day_id')
        visit_day = VisitDay.objects.get(pk=visit_day_id)
        context['visit_day'] = visit_day
        context['assignments'] = visit_day.assignments.all()
        return context

    def form_valid(self, form):
        form.instance.assigned_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('visit_day_detail', kwargs={'visit_day_id': self.object.visit_day.id})

class AssignedCompetenceDetailView(LoginRequiredMixin, DetailView):
    model = AssignedCompetence
    template_name = 'mentorship/assigned_competence_view.html'
    context_object_name = 'assignment'


class AssignedCompetenceUpdateView(LoginRequiredMixin, UpdateView):
    model = AssignedCompetence
    form_class = AssignedCompetenceForm
    template_name = 'mentorship/assigned_competence_form.html'  # create this template

    def get_success_url(self):
        # After update, redirect to the visit day detail page
        return reverse('visit_day_detail', kwargs={'visit_day_id': self.object.visit_day.id})


class MentorGradeView(LoginRequiredMixin, UpdateView):
    model = AssignedCompetence
    form_class = MentorGradeForm
    template_name = 'mentorship/mentor_grade.html'
    context_object_name = 'assignment'

    def get_queryset(self):
        # Only allow mentor to grade
        return AssignedCompetence.objects.filter(visit_day__visit__mentor=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        assignment = self.get_object()

        # Restrict access if self-assessment isn't done
        if not assignment.is_self_assessed:
            messages.warning(request, "Mentee must complete self-assessment before mentor grading.")
            return redirect('visit_day_detail', visit_day_id=assignment.visit_day.id)

        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('visit_day_detail', kwargs={'visit_day_id': self.object.visit_day.id})
    
class MenteeSelfAssessmentView(LoginRequiredMixin, UpdateView):
    model = AssignedCompetence
    form_class = MenteeSelfAssessmentForm
    template_name = 'mentorship/mentee_self_assess.html'

    def get_queryset(self):
        # Only allow mentee to self-assess
        return AssignedCompetence.objects.filter(mentee=self.request.user)

    def form_valid(self, form):
        form.instance.is_self_assessed = True  # ✅ Mark as self-assessed
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        assignment = self.get_object()
        if assignment.is_self_assessed:
            return HttpResponseForbidden("Self-assessment already submitted.")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('visit_day_detail', kwargs={'visit_day_id': self.object.visit_day.id})