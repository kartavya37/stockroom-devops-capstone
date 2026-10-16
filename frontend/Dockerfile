# ---------------------------------------------------------------------------
# StockRoom frontend image. This is a multi-stage build.
# Stage 1 makes the static files with Node.
# Stage 2 sends the static files with Nginx. The build tools stay out.
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------- stage 1
FROM node:22-alpine AS build

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html vite.config.js ./
COPY src ./src
RUN npm run build

# ----------------------------------------------------------------- stage 2
FROM nginx:1.30-alpine AS runtime

# Install the Alpine security updates (OpenSSL, c-ares, expat).
RUN apk upgrade --no-cache

# Remove the default configuration and add the project configuration.
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/stockroom.conf

# Copy only the static files from stage 1.
COPY --from=build /build/dist /usr/share/nginx/html

# Nginx must write a cache and a PID file. The non-root user needs these paths.
# /var/run is a link to /run, therefore the PID file goes to /tmp.
RUN mkdir -p /var/cache/nginx/client_temp \
    && chown -R nginx:nginx /var/cache/nginx /usr/share/nginx/html \
    && sed -i 's|^pid .*|pid /tmp/nginx.pid;|' /etc/nginx/nginx.conf

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
