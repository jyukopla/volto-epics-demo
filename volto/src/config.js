/**
 * Add your config changes here.
 * @module config
 * @example
 * export default function applyConfig(config) {
 *   config.settings = {
 *     ...config.settings,
 *     port: 4300,
 *     listBlockTypes: {
 *       ...config.settings.listBlockTypes,
 *       'my-list-item',
 *    }
 * }
 */

import {
  WPD_TASK_THANKS,
  WPD_TASK_WELCOME,
  WPD_TASK_TIMEOUT,
  WPD_TASK_CREATE_EVENT,
} from './constants';
import { EPICS_TASK_VIEWS } from './addons/volto-epics-addon/src/constants';
import WPDController from './components/WPDController';

// All your imports required for the config here BEFORE this line

import '@plone/volto/config';

export default function applyConfig(config) {
  // Add here your project's configuration here by modifying `config` accordingly
  config.settings.nonContentRoutes = [
    ...config.settings.nonContentRoutes,
    EPICS_TASK_VIEWS[WPD_TASK_WELCOME],
    EPICS_TASK_VIEWS[WPD_TASK_TIMEOUT],
    EPICS_TASK_VIEWS[WPD_TASK_THANKS],
    EPICS_TASK_VIEWS[WPD_TASK_CREATE_EVENT],
  ];
  config.settings.appExtras = [
    ...config.settings.appExtras,
    {
      match: '',
      component: WPDController,
    },
  ];

  return config;
}
