FROM python:3.9

WORKDIR /type4py/
# Put the required models files in a folder "t4py_model_files" inside "/type4py"
# -type4py/
# --type4py/
# ---t4py_model_files/
COPY . /type4py
ENV T4PY_DOCKER_MODE="1"

RUN pip install -r requirements.txt
RUN pip install -r type4py/server/requirements.txt

RUN pip install -e .

# Install NLTK corpus
RUN python -c "import nltk; nltk.download('stopwords')"
RUN python -c "import nltk; nltk.download('wordnet')"
RUN python -c "import nltk; nltk.download('omw-1.4')"
RUN python -c "import nltk; nltk.download('averaged_perceptron_tagger')"

WORKDIR /type4py/type4py/server/

EXPOSE 5010

CMD ["gunicorn", "-b 0.0.0.0:5010", "-w 2", "-k gevent", "wsgi:app", "--timeout 120"]