import { useEffect, useState } from 'react';
import { useLocation } from 'react-router';
import request from 'superagent';
import {
  EPICS_PATH_CANCEL,
  EPICS_PATH_CONTINUE,
  EPICS_PATH_MESSAGE,
  EPICS_PATH_REDIRECT,
  EPICS_PATH_START,
  EPICS_PATH_TASK,
} from './constants';
import config from '@plone/volto/registry';

/**
 * Start an EPIC.
 * @function startEpic
 * @params {string} processDefinitionKey Epic process definition key.
 * @params {object} variables Variables to pass for process start event.
 * @params {boolean} continuation Whether to redirect after call.
 */
export const startEpic = async (
  processDefinitionKey,
  variables,
  continuation = true,
) => {
  const response = await request
    .post(`${config.settings.publicPath}${EPICS_PATH_START}`)
    .send({
      processDefinitionKey,
      variables,
    });
  if (continuation) {
    if (response?.body?.location?.href) {
      window.location = response?.body?.location?.href;
    } else {
      // Nowhere to continue; Possibly an error should be shown.
    }
  }
};

/**
 * Use the current EPIC continuation status to know the next available task.
 * @function useContinuation
 * @returns {Object} Continuation response with next { location { href pathname } }.
 */
export const useContinuation = () => {
  const [continuation, setContinuation] = useState(null);
  const [timestamp, setTimestamp] = useState(null);
  const location = useLocation();
  useEffect(() => {
    (async () => {
      const now = Math.floor(new Date().getTime() / 1000);
      // Because this is used by ContinuationStatus, this is part of every page and
      // therefore the state could behave surprisingly. Throttling updates seem to
      // remove weird behavior.
      if (!timestamp || now > timestamp) {
        setContinuation({});
        setTimestamp(Math.floor(new Date().getTime() / 1000));
        try {
          const { body } = await request
            .get(`${config.settings.publicPath}${EPICS_PATH_REDIRECT}`)
            .set('Accept', 'application/json');
          setContinuation(body);
        } catch (e) {
          setContinuation({});
        }
      }
    })();
  }, [continuation, location, timestamp]);
  return continuation;
};

/**
 * Use the current EPIC continuation status to know the next available task.
 * @function useContinuationPoll
 * @returns {Object} Continuation response with next { location { href pathname } }.
 */
export const useContinuationPoll = (force) => {
  const [continuation, setContinuation] = useState(null);
  const [counter, setCounter] = useState(0);
  useEffect(() => {
    (async () => {
      try {
        const { body } = await request
          .get(`${config.settings.publicPath}${EPICS_PATH_REDIRECT}`)
          .set('Accept', 'application/json');
        setContinuation({
          ...body,
          counter,
        });
        if (Object.keys(body).length === 0) {
          setTimeout(() => setCounter(counter + 1), 3000);
        } else if (
          !!force ||
          body?.location?.pathname === EPICS_PATH_CONTINUE
        ) {
          setTimeout(() => setCounter(counter + 1), 3000);
        }
      } catch (e) {
        setContinuation({ counter });
        setTimeout(() => setCounter(counter + 1), 3000);
      }
    })();
  }, [counter]);
  return continuation;
};

/**
 * Use the first available EPIC task details.
 * @function useTask
 * @params {string} taskDefinitionKey The first task definition key to query.
 * @params {string} taskDefinitionKey The second task definition key to query.
 * @params ...
 * @returns {Object} Found task object to use.
 */
export const useTask = (...taskDefinitionKeys) => {
  const [task, setTask] = useState(null);
  useEffect(() => {
    if (task === null && taskDefinitionKeys.filter((key) => !!key).length) {
      // ^ empty deps should have been enough, but somehow wasn't...
      (async () => {
        for (const key of taskDefinitionKeys) {
          try {
            const { body } = await request
              .get(`${config.settings.publicPath}${EPICS_PATH_TASK}/${key}`)
              .set('Accept', 'application/json');
            if (
              body?.completed &&
              taskDefinitionKeys.indexOf(key) < taskDefinitionKeys.length - 1
            ) {
              // When more than one taskDefinitionKeys are polled, choose the
              // first that is not yet completed (or the last one).
              continue;
            }
            setTask(body);
            return;
          } catch (e) {}
        }
        // Task not available. Force continuation.
        // Set window.location to force hitting middleware routes
        window.location = `${config.settings.publicPath}${EPICS_PATH_REDIRECT}`;
      })();
    }
  }, [task]);
  return task;
};

/**
 * Complete an EPIC task.
 * @function completeTask
 * @params {string} taskDefinitionKey Task definition key of task to complete.
 * @params {object} variables Variables to pass for task completion.
 * @params ...
 * @returns {undefined} Call redirects to continuation poll.
 */
export const completeTask = async (
  taskDefinitionKey,
  variables,
  continuation = true,
) => {
  await request
    .post(
      `${config.settings.publicPath}${EPICS_PATH_TASK}/${taskDefinitionKey}`,
    )
    .send(variables);
  if (continuation) {
    window.location = `${config.settings.publicPath}${EPICS_PATH_REDIRECT}`;
  }
};

/**
 * Convert YYYY-MM-DD date into task completion form compatible dd/MM/YYYY
 * @function toTaskFormDate
 * @param {string} date Date in YYYY-MM-DD format.
 * @returns {string} Date in DD/MM/YYYY format.
 */
export const toTaskFormDate = (date) => {
  const result = /(\d{4})-(\d{2})-(\d{2})/.exec(date);
  return [result[3], result[2], result[1]].join('/');
};

/**
 * Send message
 * @function sendMessage
 * @returns {undefined} Redirects to known return URL.
 */
export const sendMessage = async (
  messageName,
  variables,
  continuation = true,
) => {
  const response = await request
    .post(`${config.settings.publicPath}${EPICS_PATH_MESSAGE}/${messageName}`)
    .send(variables);
  if (continuation) {
    if (response?.body?.location?.href) {
      window.location =
        response?.body?.location?.href ?? `${config.settings.publicPath}/`;
    } else {
      window.location = `${config.settings.publicPath}${EPICS_PATH_REDIRECT}`;
    }
  }
};

/**
 * Cancel the current EPIC.
 * @function cancelEpic
 * @returns {undefined} Redirects to known return URL.
 */
export const cancelEpic = async () => {
  // Canceling with message recommended instead.
  const response = await request.post(
    `${config.settings.publicPath}${EPICS_PATH_CANCEL}`,
  );
  window.location =
    response?.body?.location?.href ?? `${config.settings.publicPath}/`;
};
