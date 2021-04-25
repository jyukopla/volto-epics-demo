# NOTE: This does not result in a production image
FROM node:14.15.5-alpine3.11
WORKDIR /app
RUN apk add tini python make g++
ADD package.json package-lock.json ./
RUN npm ci
ADD .eslintrc.js ./
ADD babel.config.js ./
ADD jsconfig.json ./
ADD razzle.config.js ./
ADD public ./public
ADD theme ./theme
ADD locales ./locales
ADD src ./src
RUN npm run-script build
CMD ["/sbin/tini", "--", "npm", "run-script", "start:prod"]
