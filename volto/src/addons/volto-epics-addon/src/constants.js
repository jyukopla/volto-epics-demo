export const VOLTO_COOKIE_AUTH_TOKEN = 'auth_token';
export const EPICS_COOKIE_PROCESS_ID = 'processId';
export const EPICS_COOKIE_BUSINESS_KEY = 'businessKey';

export const EPICS_PATH_PREFIX = '/i';
export const EPICS_PATH_HEALTHZ = `${EPICS_PATH_PREFIX}/healthz`;
export const EPICS_PATH_START = `${EPICS_PATH_PREFIX}/process`;
export const EPICS_PATH_CONTINUE = `${EPICS_PATH_PREFIX}/continue`;
export const EPICS_PATH_TASK = `${EPICS_PATH_PREFIX}/task`;
export const EPICS_PATH_MESSAGE = `${EPICS_PATH_PREFIX}/message`;
export const EPICS_PATH_CANCEL = `${EPICS_PATH_PREFIX}/give-up`;
export const EPICS_PATH_REDIRECT = `${EPICS_PATH_PREFIX}/redirect`;
export const EPICS_PATH_ERROR = `${EPICS_PATH_PREFIX}/stop-by-unexpected-error`;
export const EPICS_PATH_RAISE = `${EPICS_PATH_PREFIX}/report-unexpected-error`;

export const EPICS_TASK_VIEWS = {};
export const EPICS_DEFINITIONS = {};
export const EPICS_TOAST_PROPS = {};
export const EPIC_TOAST_STATUS_MESSAGE = 'epicsToastStatus';
export const EPIC_TOAST_CONTINUATION = 'epicsToastContinuation';
