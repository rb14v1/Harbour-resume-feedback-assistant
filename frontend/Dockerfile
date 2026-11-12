# Base images pinned to exact releases instead of floating tags (sec.no_critical_cves).
FROM node:22.21.1-alpine AS dev
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
EXPOSE 8080
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM node:22.21.1-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.28.0-alpine AS prod
RUN apk upgrade --no-cache
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080

RUN sed -i 's#^pid .*#pid /tmp/nginx.pid;#' /etc/nginx/nginx.conf
RUN mkdir -p /tmp/nginx-cache && chown -R nginx:nginx /tmp/nginx-cache /usr/share/nginx/html \
    && printf 'client_body_temp_path /tmp/nginx-cache/client_temp;\nproxy_temp_path /tmp/nginx-cache/proxy_temp;\nfastcgi_temp_path /tmp/nginx-cache/fastcgi_temp;\nuwsgi_temp_path /tmp/nginx-cache/uwsgi_temp;\nscgi_temp_path /tmp/nginx-cache/scgi_temp;\n\nserver {\n    listen 0.0.0.0:8080;\n    server_name _;\n    root /usr/share/nginx/html;\n    index index.html;\n\n    client_body_temp_path /tmp/nginx-cache/client_temp;\n    proxy_temp_path /tmp/nginx-cache/proxy_temp;\n    fastcgi_temp_path /tmp/nginx-cache/fastcgi_temp;\n    uwsgi_temp_path /tmp/nginx-cache/uwsgi_temp;\n    scgi_temp_path /tmp/nginx-cache/scgi_temp;\n\n    location / {\n        try_files $uri $uri/ /index.html;\n    }\n}\n' > /etc/nginx/conf.d/default.conf
USER nginx
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
