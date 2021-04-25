import {
  EPICS_COOKIE_BUSINESS_KEY,
  EPICS_COOKIE_PROCESS_ID,
  EPICS_PATH_ERROR,
} from 'volto-epics-addon/constants';
import request from 'superagent';
import config from '@plone/volto/registry';
import { v4 as uuid } from 'uuid';
import { getCookie, redact } from 'volto-epics-addon/middleware/helpers';

/* eslint-disable no-console */

export default async (req, res, next) => {
  const processId = getCookie(req, EPICS_COOKIE_PROCESS_ID);
  const businessKey = getCookie(req, EPICS_COOKIE_BUSINESS_KEY);
  const uid = uuid();
  if (processId && businessKey) {
    try {
      const { body } = await request.get(
        `${config.settings.processApiPath}/process/${processId}/${businessKey}`,
      );
      console.error(new Date(), '[epic]', 'raise', redact(body));
    } catch (e) {
      console.error(new Date(), '[epic]', 'raise', uid, e.error);
    }
  } else {
    console.error(new Date(), '[epic]', 'raise', uid, {
      processId,
      businessKey,
    });
  }
  res.redirect(302, `${config.settings.publicPath}${EPICS_PATH_ERROR}/${uid}`);
};
