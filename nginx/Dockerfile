FROM nginx:1.19.6-alpine

COPY sites-enabled/ /etc/nginx/sites-enabled/
COPY nginx.conf /etc/nginx/
COPY docker-entrypoint.sh /

ENTRYPOINT [ "/docker-entrypoint.sh" ]
