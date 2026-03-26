FROM node:20-slim AS development
WORKDIR /app

COPY package*.json ./
RUN rm -rf node_modules package-lock.json && \
    npm install --legacy-peer-deps

COPY .env* ./

EXPOSE 8080

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
