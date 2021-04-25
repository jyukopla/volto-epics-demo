import {
  EPICS_DEFINITIONS as EPICS,
  EPICS_TASK_VIEWS as TASKS,
  EPICS_TOAST_PROPS as TOAST,
} from 'volto-epics-addon/constants';

export const WORLD_PLONE_DAY = 'world-plone-day';
EPICS[WORLD_PLONE_DAY] = WORLD_PLONE_DAY;

export const WPD_TASK_THANKS = 'wpdTaskThanks';
TASKS[WPD_TASK_THANKS] = '/wpd-thank-you';
TOAST[WPD_TASK_THANKS] = {
  title: 'World Plone Day in progress',
  showCancel: false,
};

export const WPD_TASK_WELCOME = 'wpdTaskWelcome';
TASKS[WPD_TASK_WELCOME] = '/wpd-welcome';
TOAST[WPD_TASK_WELCOME] = {
  title: 'World Plone Day in progress',
  showCancel: true,
};

export const WPD_TASK_EVENTS = 'wpdTaskEvents';
TASKS[WPD_TASK_EVENTS] = '/events';
TOAST[WPD_TASK_EVENTS] = {
  title: 'World Plone Day in progress',
  showCancel: true,
};

export const WPD_TASK_TIMEOUT = 'wpdTaskTimeout';
TASKS[WPD_TASK_TIMEOUT] = '/timeout';
TOAST[WPD_TASK_TIMEOUT] = {
  title: 'World Plone Day in progress',
  showCancel: true,
};

export const WPD_TASK_CREATE_EVENT = 'wpdEventForm';
TASKS[WPD_TASK_CREATE_EVENT] = '/wdp-event-form';
TOAST[WPD_TASK_CREATE_EVENT] = {
  title: 'World Plone Day in progress',
  showCancel: true,
};
