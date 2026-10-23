from django.contrib.auth.mixins import LoginRequiredMixin
from utils import access
from utils.access_mixins import FeatureAccessMixin
from django.views.generic import ListView,CreateView, UpdateView, DetailView, DeleteView, View
from django.urls import reverse_lazy
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from .models import UserManual
from .forms import UserManualCreateForm, UserManualUpdateForm
import os
from django.contrib import messages


class UserManualListView(LoginRequiredMixin, ListView):
    model = UserManual
    template_name = 'documents/manuals/usermanual_list.html'  # Your template to display list
    context_object_name = 'manuals'  # The variable name in the template
    paginate_by = 10  # Optional: paginate 10 per page
    
class UserManualCreateView(FeatureAccessMixin, CreateView):
    access_feature = access.SYSTEM_ADMIN
    model = UserManual
    form_class = UserManualCreateForm
    template_name = 'documents/manuals/usermanual_form.html'
    success_url = reverse_lazy('documents:usermanual-list')  # Lazy to avoid circular imports

class UserManualUpdateView(FeatureAccessMixin, UpdateView):
    access_feature = access.SYSTEM_ADMIN
    model = UserManual
    form_class = UserManualUpdateForm
    template_name = 'documents/manuals/usermanual_form.html'
    success_url = reverse_lazy('documents:usermanual-list')  # Lazy to avoid circular imports

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['manual_id'] = self.object.pk
        return kwargs

class UserManualDetailView(LoginRequiredMixin, DetailView):
    model = UserManual
    template_name = 'documents/manuals/usermanual_detail.html'


class UserManualDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk):
        manual = get_object_or_404(UserManual, pk=pk)
        file_path = manual.file.path
        if os.path.exists(file_path):
            # Serve the file for download as PDF
            return FileResponse(open(file_path, 'rb'), content_type='application/pdf', as_attachment=True, filename=os.path.basename(file_path))
        else:
            raise Http404("File does not exist")
        
        
class UserManualDeleteView(FeatureAccessMixin, DeleteView):
    access_feature = access.SYSTEM_ADMIN
    model = UserManual
    template_name = 'documents/manuals/usermanual_confirm_delete.html'
    success_url = reverse_lazy('documents:usermanual-list')

    def delete(self, request, *args, **kwargs):
        manual = self.get_object()

        # Delete the file from disk
        if manual.file and os.path.isfile(manual.file.path):
            os.remove(manual.file.path)

        # Success message
        messages.success(request, f"Manual '{manual.title}' was deleted successfully.")

        return super().delete(request, *args, **kwargs)
