# Builds the container image defined by frontend/Dockerfile with only the dependencies required for its target runtime.

FROM nginx:1.27-alpine

# The production frontend is pre-built and included in this delivery.
# This avoids downloading Node dependencies during Docker startup.
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=20s --timeout=3s --retries=3 \
  CMD wget -q -O - http://127.0.0.1:8080/healthz || exit 1
