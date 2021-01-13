mobile distributed computing platform (mdcp)

##
`docker-compose -f docker-compose.dev.yaml up -d --build`

## environment variables description
- run `cp .env.example .env`
- fill `.env` file

## steps to create site admin (/admin)
- get a shell with `docker exec -it mdcp-panel_web_1 bash`
- run `python manage.py createsuperuser`
- enter your username, email and a strong password

## .
- open ports 7979 to access web microservice. `sudo ufw allow 7979`
- open 1883 to access mqtt broker. `sudo ufw allow 1883`
