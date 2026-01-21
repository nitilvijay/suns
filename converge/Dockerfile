FROM python:3.13.11

WORKDIR /backend/

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /backend

# Setup an app user so the container doesn't run as the root user
RUN useradd app
USER app

# Expose port for the Django/Gunicorn app
EXPOSE 8000

# Run migrations and start Gunicorn
CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 --workers 3 converge.wsgi:application"]
