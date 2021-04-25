import express from 'express';
import {
  EPICS_PATH_CANCEL,
  EPICS_PATH_HEALTHZ,
  EPICS_PATH_MESSAGE,
  EPICS_PATH_RAISE,
  EPICS_PATH_REDIRECT,
  EPICS_PATH_START,
  EPICS_PATH_TASK,
} from 'volto-epics-addon/constants';
import continuation from 'volto-epics-addon/middleware/continuation';
import start from 'volto-epics-addon/middleware/start';
import task from 'volto-epics-addon/middleware/task';
import raise from 'volto-epics-addon/middleware/raise';
import complete from 'volto-epics-addon/middleware/complete';
import cancel from 'volto-epics-addon/middleware/cancel';
import message from 'volto-epics-addon/middleware/message';
import healthz from 'volto-epics-addon/middleware/healthz';

const factory = (publicPath) => {
  const m = express.Router();
  m.use(express.json());
  // PROCESS GENERIC
  m.get(`${publicPath}${EPICS_PATH_HEALTHZ}`, healthz);
  m.post(`${publicPath}${EPICS_PATH_START}`, start);
  m.get(`${publicPath}${EPICS_PATH_REDIRECT}`, continuation);
  m.post(`${publicPath}${EPICS_PATH_CANCEL}`, cancel);
  m.get(`${publicPath}${EPICS_PATH_RAISE}`, raise);
  m.post(`${publicPath}${EPICS_PATH_MESSAGE}/:message_id`, message);
  m.get(`${publicPath}${EPICS_PATH_TASK}/:task_definition_key`, task);
  m.post(`${publicPath}${EPICS_PATH_TASK}/:task_definition_key`, complete);
  m.id = 'volto-epics-addon-middleware';
  return m;
};

export default factory;
