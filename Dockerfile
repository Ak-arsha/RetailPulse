FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN python generate_data.py && python pipeline.py
ENV PORT=8080
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
