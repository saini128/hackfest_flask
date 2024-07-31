
FROM python:3.11-slim
RUN apt-get update && \
	    apt-get install -y libglib2.0-0 libgl1-mesa-glx

WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY . .

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
