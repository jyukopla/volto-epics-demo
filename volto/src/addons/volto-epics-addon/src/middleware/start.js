import {
  EPICS_COOKIE_BUSINESS_KEY,
  EPICS_COOKIE_PROCESS_ID,
  EPICS_DEFINITIONS,
  EPICS_PATH_ERROR,
  EPICS_PATH_PREFIX,
  EPICS_PATH_REDIRECT,
  VOLTO_COOKIE_AUTH_TOKEN,
} from 'volto-epics-addon/constants';
import config from '@plone/volto/registry';
import request from 'superagent';
import { v4 as uuid } from 'uuid';
import jwtDecode from 'jwt-decode';
import {
  getCookie,
  redact,
  setCookie,
} from 'volto-epics-addon/middleware/helpers';

/* eslint-disable no-console */

export default async (req, res, next) => {
  const processId = getCookie(req, EPICS_COOKIE_PROCESS_ID);
  const businessKey = getCookie(req, EPICS_COOKIE_BUSINESS_KEY);

  // Maybe continue old process
  if (processId && businessKey) {
    let epic;
    try {
      const { body } = await request.get(
        `${config.settings.processApiPath}/process/${processId}/${businessKey}`,
      );
      // Prefer root process id
      epic = body;
      if (epic.rootProcessInstanceId !== processId) {
        const { body } = await request.get(
          `${config.settings.processApiPath}/process/${epic.rootProcessInstanceId}/${businessKey}`,
        );
        epic = body;
        if (epic?.state === 'ACTIVE') {
          setCookie(req, res, EPICS_COOKIE_PROCESS_ID, epic.id);
        }
      }
    } catch (e) {}
    if (epic?.state === 'ACTIVE') {
      res.send({
        location: {
          href: `${config.settings.publicPath}${EPICS_PATH_REDIRECT}`,
          pathname: EPICS_PATH_REDIRECT,
        },
      });
      return;
    }
  }

  // Resolve logged-in user details
  let email, username, firstName, lastName;
  const authToken = getCookie(req, VOLTO_COOKIE_AUTH_TOKEN);
  if (authToken) {
    try {
      const { body: user } = await request
        .get(`${config.settings.apiPath}/@users/${jwtDecode(authToken).sub}`)
        .set('Accept', 'application/json')
        .set('Authorization', `Bearer ${authToken}`);
      email = user.email;
      username = user.username;
      if (user.fullname) {
        if (user.fullname.match(/, /)) {
          firstName = user.fullname.split(', ').slice(1).join(', ');
          lastName = user.fullname.split(', ')[0];
        } else {
          const parts = user.fullname.split(' ');
          firstName = parts.slice(0, parts.length - 1).join(' ');
          lastName = parts[parts.length - 1];
        }
      }
    } catch (e) {
      // Invalid token; Start process as anonymous user
      console.error(new Date(), '[epic]', 'start', e);
    }
  }

  // Start Epic
  const { processDefinitionKey, variables } = req.body;
  if (EPICS_DEFINITIONS[processDefinitionKey] && variables) {
    const baseUrl = `${
      req.headers.origin || req.protocol + '://' + req.headers.host
    }${config.settings.publicPath}${EPICS_PATH_PREFIX}`;
    const payload = {
      processDefinitionKey: processDefinitionKey,
      variables:
        email && username && firstName && lastName
          ? {
              ...variables,
              baseUrl,
              email,
              username,
              firstName,
              lastName,
            }
          : {
              ...variables,
              baseUrl,
            },
    };
    console.log(new Date(), '[epic]', 'start', redact(payload));
    try {
      const { body: epic } = await request
        .post(`${config.settings.processApiPath}/process`)
        .send(payload);
      setCookie(req, res, EPICS_COOKIE_PROCESS_ID, epic.id);
      setCookie(req, res, EPICS_COOKIE_BUSINESS_KEY, epic.businessKey);
      res.send({
        location: {
          href: `${config.settings.publicPath}${EPICS_PATH_REDIRECT}`,
          pathname: EPICS_PATH_REDIRECT,
        },
      });
      return;
    } catch (e) {
      // Unexpected error
      const uid = uuid();
      console.error(
        new Date(),
        '[epic]',
        'start',
        uid,
        e?.status ?? 500,
        e?.response?.text ?? e,
      );
      res.send({
        location: {
          href: `${config.settings.publicPath}${EPICS_PATH_ERROR}/${uid}`,
          pathname: `${EPICS_PATH_ERROR}/${uid}`,
        },
      });
      return;
    }
  }
  res.send({});
};
