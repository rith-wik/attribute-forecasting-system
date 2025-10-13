FROM node:20-alpine

WORKDIR /web

# Copy package files
COPY package.json package-lock.json* /web/

# Install dependencies
RUN npm install

# Copy application code
COPY . /web

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
