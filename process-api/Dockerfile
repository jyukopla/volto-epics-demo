FROM python:3.9-alpine3.12 AS PYTHON_TOOLCHAIN
RUN apk add gcc musl-dev libffi-dev
RUN python -m venv /app
RUN /app/bin/pip install -U \
    aiohttp \
    fastapi==0.61.2 \
    pydantic \
    starlette==0.13.6 \
    uvicorn
ADD setup.py setup.cfg ./
ADD src ./src
RUN /app/bin/python setup.py install

FROM python:3.9-alpine3.12
COPY --from=PYTHON_TOOLCHAIN /app /app
ENTRYPOINT [ "/app/bin/uvicorn", "--host", "0.0.0.0", "--proxy-headers", "process_api.main:app" ]
