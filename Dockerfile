FROM python:3.12.0
EXPOSE 5000
COPY . /app
WORKDIR /app
CMD ["pip", "-h"]
#RUN pip install -r requirements.txt
#CMD ["python", "WebCralwer/WebCralwer/main.py"]
