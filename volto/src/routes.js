/**
 * Routes.
 * @module routes
 */

import { App } from '@plone/volto/components';
import { defaultRoutes } from '@plone/volto/routes';
import config from '@plone/volto/registry';
import { EPICS_TASK_VIEWS } from './addons/volto-epics-addon/src/constants';
import {
  WPD_TASK_THANKS,
  WPD_TASK_TIMEOUT,
  WPD_TASK_WELCOME,
  WPD_TASK_CREATE_EVENT,
} from './constants';
import WelcomePage from './components/WelcomePage';
import TimeoutPage from './components/TimeoutPage';
import ThanksPage from './components/ThanksPage';
import EventFormPage from './components/EventFormPage';

/**
 * Routes array.
 * @array
 * @returns {array} Routes.
 */
const routes = [
  {
    path: '/',
    component: App, // Change this if you want a different component
    routes: [
      {
        path: EPICS_TASK_VIEWS[WPD_TASK_WELCOME],
        component: WelcomePage,
      },
      {
        path: EPICS_TASK_VIEWS[WPD_TASK_TIMEOUT],
        component: TimeoutPage,
      },
      {
        path: EPICS_TASK_VIEWS[WPD_TASK_THANKS],
        component: ThanksPage,
      },
      {
        path: EPICS_TASK_VIEWS[WPD_TASK_CREATE_EVENT],
        component: EventFormPage,
      },
      // Add your routes here
      ...(config.addonRoutes || []),
      ...defaultRoutes,
    ],
  },
];

export default routes;
