version: "3"

services:
  web:
    image: nginx
    container_name: web_server_{{ENV_NAME}}{{IDENTIFIER}}
    environment:
      - ENVIRONMENT={{ENV_NAME}}
    ports:
      - "8080:80"