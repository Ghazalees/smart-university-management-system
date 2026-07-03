# Builds the container image defined by nginx/Dockerfile with only the dependencies required for its target runtime.

FROM nginx:stable-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d /etc/nginx/conf.d
