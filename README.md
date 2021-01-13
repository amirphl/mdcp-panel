mobile distributed computing platform (mdcp)

##
`docker-compose -f docker-compose.dev.yaml up -d --build`

## environment variables description

## steps to create site admin (/admin)
- get a shell with `docker exec -it mdcp-panel_web_1 bash`
- run `python manage.py createsuperuser`
- enter your username, email and a strong password

## .
- open ports 7979 to access web microservice
- open 1883 to access mqtt broker
