from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Task
from .serializers import TaskSerializer, UserRegisterSerializer
from rest_framework import generics, permissions
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

# -------------------------
# Web Views (HTML)
# -------------------------

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'task/task_list.html'
    context_object_name = 'tasks'
    ordering = ['-created_at']
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(owner=self.request.user)

        status = self.request.GET.get('status')
        if status in ['pending','in-progress','done']:
            qs = qs.filter(status=status)

        due_date = self.request.GET.get('due_date')
        if due_date:
            qs = qs.filter(due_date__date=due_date)

        return qs

class TaskCreateUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    template_name = 'task/task_form.html'
    fields = ['title', 'description', 'status', 'due_date']
    success_url = reverse_lazy('task_index')

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        if pk:
            return get_object_or_404(Task, pk=pk)
        return None

    def form_valid(self, form):
        task = form.instance
        if not task.pk:
            task.owner = self.request.user
        if task.status == 'done' and task.due_date > timezone.now():
            messages.error(self.request, "Cannot mark task as done before its due date.")
            return redirect(self.request.path)
        return super().form_valid(form)

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'task/task_confirm_delete.html'
    success_url = reverse_lazy('task_index')


# -------------------------
# API Views (JWT)
# -------------------------

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Task.objects.all()
        if not self.request.user.is_superuser:
            qs = qs.filter(owner=self.request.user)

        status = self.request.GET.get('status')
        if status in ['pending','in-progress','done']:
            qs = qs.filter(status=status)

        due_date = self.request.GET.get('due_date')
        if due_date:
            qs = qs.filter(due_date__date=due_date)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class TaskRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Task.objects.all()
        if not self.request.user.is_superuser:
            qs = qs.filter(owner=self.request.user)
        return qs
