FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --upgrade numpy pandas
COPY . .
EXPOSE 5000
#CMD ["python", "app.py"]


CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

#xomando para iniciar o Gunicorn (adicionei isto para a API funcionar no render(?)) - atualizar tambem o ficheiro requirements
#CMD ["gunicorn", "-b", "0.0.0.0:$PORT", "app:app"]
#CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-5000} app:app"]
