version: "3"

services:
  web:
    image: nginx
    container_name: web_server_{{ENV_NAME}}
    environment:
      - ENVIRONMENT={{ENV_NAME}}
    ports:
      - "8080:80"