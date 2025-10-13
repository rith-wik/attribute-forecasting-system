FROM node:20-alpine

WORKDIR /web

# Build argument for API base URL
ARG VITE_API_BASE=http://localhost:8000/api/v1

# Copy package files
COPY package.json package-lock.json* /web/

# Install dependencies
RUN npm install

# Copy application code
COPY . /web

# Set environment variable
ENV VITE_API_BASE=${VITE_API_BASE}

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
