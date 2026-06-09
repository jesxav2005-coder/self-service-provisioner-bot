version: "3"

services:
  web:
    image: nginx
    container_name: web_server
    ports:
      - "8080:80"