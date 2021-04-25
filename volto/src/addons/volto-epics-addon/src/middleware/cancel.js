import {
  EPICS_COOKIE_BUSINESS_KEY,
  EPICS_COOKIE_PROCESS_ID,
  VOLTO_COOKIE_AUTH_TOKEN,
} from 'volto-epics-addon/constants';
import request from 'superagent';
import config from '@plone/volto/registry';
import {
  getCookie,
  redact,
  resolveUUID,
} from 'volto-epics-addon/middleware/helpers';

/* eslint-disable no-console */

export default async (req, res, next) => {
  const processId = getCookie(req, EPICS_COOKIE_PROCESS_ID);
  const businessKey = getCookie(req, EPICS_COOKIE_BUSINESS_KEY);
  if (processId && businessKey) {
    let contentUid;
    try {
      const { body: epic } = await request.delete(
        `${config.settings.processApiPath}/process/${processId}/${businessKey}`,
      );
      console.log(new Date(), '[epic]', 'cancel', redact(epic));
      contentUid = epic?.variables?.contentUid;
    } catch (e) {}
    const authToken = getCookie(req, VOLTO_COOKIE_AUTH_TOKEN);
    const pathname = await resolveUUID(contentUid, authToken);
    if (pathname) {
      res.send({
        location: {
          href: `${config.settings.publicPath}${pathname}`,
          pathname,
        },
      });
    } else {
      res.send({});
    }
  } else {
    res.send({});
  }
};
