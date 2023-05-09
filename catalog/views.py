import datetime

from django.contrib.auth.decorators import permission_required

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import render
from django.views import generic

from .models import Book, Author, BookInstance, Genre
from .forms import RenewBookForm, RenewBookModelForm


def index(request):
    """
    Функция отображения для домашней страницы сайта.
    """
    # Генерация "количеств" некоторых главных объектов
    num_books = Book.objects.all().count()
    num_books_contain = Book.objects.filter(title__icontains='Жизнь').count()
    num_instances = BookInstance.objects.all().count()
    # Доступные книги (статус = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()  # Метод 'all()' применён по умолчанию.

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    # Отрисовка HTML-шаблона index.html с данными внутри
    # переменной контекста context
    context = {
        'num_books': num_books,
        'num_books_contain': num_books_contain,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }
    return render(request, 'catalog/index.html', context=context)


class BookListView(generic.ListView):

    model = Book
    paginate_by = 10


class BookDetailView(generic.DetailView):

    model = Book


class AuthorListView(generic.ListView):

    model = Author
    paginate_by = 10
    # template_name = ''


class AuthorDetailView(generic.DetailView):

    model = Author


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to current user.
    """
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class LoanedBooksForLibrarianListView(PermissionRequiredMixin, generic.ListView):

    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_for_librarian.html'
    paginate_by = 10
    permission_required = 'catalog.can_mark_returned'

    def get_queryset(self):
        return BookInstance.objects.all()


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    book_inst = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookModelForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('for-librarian'))

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst': book_inst})


class AuthorCreate(CreateView):

    model = Author
    fields = '__all__'
    initial = {'date_of_death': '12/10/2016', }


class AuthorUpdate(UpdateView):

    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']


class AuthorDelete(DeleteView):

    model = Author
    success_url = reverse_lazy('authors')


class BookCreate(CreateView):

    model = Book
    fields = '__all__'
    template_name = 'catalog/book_create.html'


class BookUpdate(UpdateView):

    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre']
    template_name = 'catalog/book_update.html'


class BookDelete(DeleteView):

    model = Book
    success_url = reverse_lazy('books')
    template_name = 'catalog/book_delete.html'
