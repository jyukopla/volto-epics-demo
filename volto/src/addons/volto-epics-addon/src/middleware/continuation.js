import config from '@plone/volto/registry';
import request from 'superagent';
import { v4 as uuid } from 'uuid';
import {
  EPICS_COOKIE_BUSINESS_KEY,
  EPICS_COOKIE_PROCESS_ID,
  EPICS_PATH_CONTINUE,
  EPICS_PATH_ERROR,
  EPICS_TASK_VIEWS,
  VOLTO_COOKIE_AUTH_TOKEN,
} from 'volto-epics-addon/constants';
import {
  clearCookie,
  getCookie,
  redact,
  resolveUUID,
  setCookie,
} from 'volto-epics-addon/middleware/helpers';

/* eslint-disable no-console */

export default async (req, res, next) => {
  const processId = getCookie(req, EPICS_COOKIE_PROCESS_ID);
  const businessKey = getCookie(req, EPICS_COOKIE_BUSINESS_KEY);
  const json = !!req.headers['accept'].match(/application\/json/);

  //
  // No cookie, no process
  //
  if (!processId || !businessKey) {
    clearCookie(req, res, EPICS_COOKIE_PROCESS_ID);
    clearCookie(req, res, EPICS_COOKIE_BUSINESS_KEY);
    if (json) {
      res.send({
        errorCode: null,
        errorMessage: null,
        statusCode: null,
        statusMessage: null,
        location: {
          href: `${config.settings.publicPath}/`,
          pathname: `/`,
        },
        taskDefinitionKey: null,
      });
    } else {
      res.redirect(302, `${config.settings.publicPath}/`);
    }
  } else {
    setCookie(req, res, EPICS_COOKIE_PROCESS_ID, processId);
    setCookie(req, res, EPICS_COOKIE_BUSINESS_KEY, businessKey);
    //
    // Cookie, maybe process
    //
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
    } catch (e) {
      //
      // 404 Invalid cookie
      //
      const uid = uuid();
      if (e?.status === 404) {
        clearCookie(req, res, EPICS_COOKIE_PROCESS_ID);
        clearCookie(req, res, EPICS_COOKIE_BUSINESS_KEY);
      }
      console.error(
        new Date(),
        '[epic]',
        'continuation',
        uid,
        e?.status ?? 500,
        e?.response?.text ?? e,
      );
      if (json) {
        res.send({
          errorCode: null,
          errorMessage: null,
          statusCode: null,
          statusMessage: null,
          location: {
            href: `${config.settings.publicPath}${EPICS_PATH_ERROR}/${uid}`,
            pathname: `${EPICS_PATH_ERROR}/${uid}`,
          },
          taskDefinitionKey: null,
        });
      } else {
        res.redirect(
          302,
          `${config.settings.publicPath}${EPICS_PATH_ERROR}/${uid}`,
        );
      }
    }
    if (epic?.state === 'ACTIVE') {
      //
      // 200 Active process
      //
      for (const task of epic?.tasks ?? []) {
        const key = task.taskDefinitionKey;
        console.log(
          new Date(),
          '[epic]',
          'continuation',
          key,
          EPICS_TASK_VIEWS[key],
        );
        if (EPICS_TASK_VIEWS[key]) {
          if (json) {
            let task_;
            try {
              const { body } = await request.get(
                `${config.settings.processApiPath}/process/${processId}/${businessKey}/tasks/${key}`,
              );
              task_ = body;
            } catch (e) {
              task_ = {};
            }
            res.send({
              errorCode:
                task_?.variables?.errorCode ??
                epic?.variables?.errorCode ??
                null,
              errorMessage:
                task_?.variables?.errorMessage ??
                epic?.variables?.errorMessage ??
                null,
              statusCode:
                task_?.variables?.statusCode ??
                epic?.variables?.statusCode ??
                null,
              statusMessage:
                task_?.variables?.statusMessage ??
                epic?.variables?.statusMessage ??
                null,
              location: {
                href: `${config.settings.publicPath}${EPICS_TASK_VIEWS[key]}`,
                pathname: EPICS_TASK_VIEWS[key],
              },
              taskDefinitionKey: key,
            });
          } else {
            res.redirect(
              302,
              `${config.settings.publicPath}${EPICS_TASK_VIEWS[key]}`,
            );
          }
          break;
        } else {
          // Task not yet implemented error
          const uid = uuid();
          console.error(
            new Date(),
            '[epic]',
            'continuation',
            uid,
            `${key} not implemented`,
          );
          if (json) {
            res.send({
              errorCode: epic?.variables?.errorCode ?? null,
              errorMessage: epic?.variables?.errorMessage ?? null,
              statusCode: epic?.variables?.statusCode ?? null,
              statusMessage: epic?.variables?.statusMessage ?? null,
              location: {
                href: `${config.settings.publicPath}${EPICS_PATH_ERROR}/${uid}`,
                pathname: `${EPICS_PATH_ERROR}/${uid}`,
              },
              taskDefinitionKey: null,
            });
          } else {
            res.redirect(
              302,
              `${config.settings.publicPath}${EPICS_PATH_ERROR}/${uid}`,
            );
          }
          break;
        }
      }
      if ((epic?.tasks ?? []).length === 0) {
        // Possible task not yet available
        console.log(new Date(), '[epic]', 'continuation', redact(epic));
        if (json) {
          res.send({
            errorCode: epic?.variables?.errorCode ?? null,
            errorMessage: epic?.variables?.errorMessage ?? null,
            statusCode: epic?.variables?.statusCode ?? null,
            statusMessage: epic?.variables?.statusMessage ?? null,
            location: {
              href: `${config.settings.publicPath}${EPICS_PATH_CONTINUE}`,
              pathname: `${EPICS_PATH_CONTINUE}`,
            },
            taskDefinitionKey: null,
          });
        } else {
          res.redirect(
            302,
            `${config.settings.publicPath}${EPICS_PATH_CONTINUE}`,
          );
        }
      }
    } else if (epic?.state === 'COMPLETED') {
      //
      // Completed process
      //
      console.log(new Date(), '[epic]', 'continuation', redact(epic));
      if (json) {
        clearCookie(req, res, EPICS_COOKIE_PROCESS_ID);
        clearCookie(req, res, EPICS_COOKIE_BUSINESS_KEY);
      }
      let pathname;
      if (epic?.variables?.contentUid) {
        const authToken = getCookie(req, VOLTO_COOKIE_AUTH_TOKEN);
        pathname = await resolveUUID(epic.variables.contentUid, authToken);
      }
      if (pathname) {
        if (json) {
          res.send({
            errorCode: epic?.variables?.errorCode ?? null,
            errorMessage: epic?.variables?.errorMessage ?? null,
            statusCode: epic?.variables?.statusCode ?? null,
            statusMessage: epic?.variables?.statusMessage ?? null,
            location: {
              href: `${config.settings.publicPath}${pathname}`,
              pathname,
            },
            taskDefinitionKey: null,
          });
        } else {
          res.redirect(302, `${config.settings.publicPath}${pathname}`);
        }
      } else {
        if (json) {
          res.send({
            errorCode: epic?.variables?.errorCode ?? null,
            errorMessage: epic?.variables?.errorMessage ?? null,
            statusCode: epic?.variables?.statusCode ?? null,
            statusMessage: epic?.variables?.statusMessage ?? null,
            location: {
              href: `${config.settings.publicPath}/`,
              pathname: '/',
            },
            taskDefinitionKey: null,
          });
        } else {
          res.redirect(302, `${config.settings.publicPath}/`);
        }
      }
    } else if (!!epic?.state) {
      //
      // Terminated process
      //
      // SUSPENDED
      // EXTERNALLY_TERMINATED
      // INTERNALLY_TERMINATED
      console.log(new Date(), '[epic]', 'continuation', redact(epic));
      if (json) {
        clearCookie(req, res, EPICS_COOKIE_PROCESS_ID);
        clearCookie(req, res, EPICS_COOKIE_BUSINESS_KEY);
      }
      const contentUid = epic?.variables?.contentUid;
      if (contentUid) {
        const authToken = getCookie(req, VOLTO_COOKIE_AUTH_TOKEN);
        const pathname = await resolveUUID(contentUid, authToken);
        if (pathname) {
          if (json) {
            res.send({
              errorCode: epic?.variables?.errorCode ?? null,
              errorMessage: epic?.variables?.errorMessage ?? null,
              statusCode: epic?.variables?.statusCode ?? null,
              statusMessage: epic?.variables?.statusMessage ?? null,
              location: {
                href: `${config.settings.publicPath}${pathname}`,
                pathname,
              },
              taskDefinitionKey: null,
            });
            return;
          } else {
            res.redirect(302, `${config.settings.publicPath}${pathname}`);
            return;
          }
        }
      }
      if (json) {
        res.send({
          errorCode: epic?.variables?.errorCode ?? null,
          errorMessage: epic?.variables?.errorMessage ?? null,
          location: {
            href: `${config.settings.publicPath}/`,
            pathname: '/',
          },
          taskDefinitionKey: null,
        });
      } else {
        res.redirect(302, `${config.settings.publicPath}/`);
      }
    }
  }
};
