FROM node:22-slim

RUN npm install -g http-server

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker caching
COPY ./frontend /app

COPY ./frontend/package*.json /app/

# Clean npm cache and install dependencies
RUN npm install

RUN npm run build

CMD ["http-server", "dist"]