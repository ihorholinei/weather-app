FROM nginx:alpine

# Скопіювати Nginx конфіг для реверс-проксі
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Скопіювати статику
COPY index.html /usr/share/nginx/html/index.html
COPY style.css /usr/share/nginx/html/style.css
COPY app.js /usr/share/nginx/html/app.js

EXPOSE 80