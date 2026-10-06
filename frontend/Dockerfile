# ---------- 构建阶段 ----------
FROM node:22-alpine AS build

WORKDIR /app

# 先装依赖，源码变化时可以利用缓存
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---------- 运行阶段 ----------
FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
