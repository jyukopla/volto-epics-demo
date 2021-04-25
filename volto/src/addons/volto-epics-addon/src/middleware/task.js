import {
  EPICS_COOKIE_BUSINESS_KEY,
  EPICS_COOKIE_PROCESS_ID,
} from '../constants';
import request from 'superagent';
import config from '@plone/volto/registry';
import { getCookie, redact } from 'volto-epics-addon/middleware/helpers';

/* eslint-disable no-console */

export default async (req, res, next) => {
  const processId = getCookie(req, EPICS_COOKIE_PROCESS_ID);
  const businessKey = getCookie(req, EPICS_COOKIE_BUSINESS_KEY);
  const { task_definition_key: taskDefinitionKey } = req.params;
  if (processId && businessKey && taskDefinitionKey) {
    try {
      const { body: task } = await request.get(
        `${config.settings.processApiPath}/process/${processId}/${businessKey}/tasks/${taskDefinitionKey}`,
      );
      console.log(new Date(), '[epic]', 'task', redact(task));
      res.send(task);
    } catch (e) {
      //
      // 400-500 Task not found
      //
      console.log(
        new Date(),
        '[epic]',
        'task',
        e?.status ?? 500,
        e?.response?.text ?? e,
      );
      res.status(e?.status ?? 404);
      res.send(
        e?.response?.type === 'application/json'
          ? JSON.parse(e?.response?.text ?? 'null')
          : e?.response?.text ?? 'n/a',
      );
    }
  } else {
    //
    // 400 Invalid cookie
    //
    res.status(400);
    res.send({ processId, businessKey, taskDefinitionKey });
  }
};
