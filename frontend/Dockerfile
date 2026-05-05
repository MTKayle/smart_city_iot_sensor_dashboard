# Multi-stage build for React frontend with Vite
# Stage 1: Build the application
FROM node:20-alpine as build

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
# Using npm install (not ci) so the build tolerates minor lockfile drift
# (e.g. when package.json deps are bumped). For a fully reproducible build
# regenerate the lockfile locally then switch back to `npm ci`.
RUN npm install --no-audit --no-fund --loglevel=error

# Copy application source code (includes .env file)
COPY . .

# Build arguments for Vite environment variables
ARG VITE_API_URL=http://localhost:8000
ARG VITE_WS_URL=ws://localhost:8000/ws
ARG VITE_MAPBOX_TOKEN

# Set environment variables for build
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL
ENV VITE_MAPBOX_TOKEN=$VITE_MAPBOX_TOKEN

# Build production bundle with Vite
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built files from build stage (Vite outputs to dist/)
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 3000
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
