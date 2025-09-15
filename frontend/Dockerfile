FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM node:20-alpine AS runtime
WORKDIR /app
RUN npm i -g serve@14.2.1
COPY --from=build /app/dist ./dist
ENV PORT=3000
EXPOSE 3000
# Bind to 0.0.0.0 so the container is accessible from outside
CMD ["sh", "-c", "serve -s dist -l tcp://0.0.0.0:$PORT"]

