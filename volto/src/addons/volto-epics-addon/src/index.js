import {
  EPICS_PATH_CANCEL,
  EPICS_PATH_CONTINUE,
  EPICS_PATH_ERROR,
  EPICS_PATH_HEALTHZ,
  EPICS_PATH_MESSAGE,
  EPICS_PATH_RAISE,
  EPICS_PATH_REDIRECT,
  EPICS_PATH_START,
  EPICS_PATH_TASK,
} from 'volto-epics-addon/constants';
import ContinuationPollPage from 'volto-epics-addon/components/theme/Epics/ContinuationPollPage';
import UnexpectedErrorPage from 'volto-epics-addon/components/theme/Epics/UnexpectedErrorPage';
import ContinuationStatus from 'volto-epics-addon/components/theme/Epics/ContinuationStatus';
import Demo from 'volto-epics-addon/components/theme/Epics/Demo';

const applyConfig = (config) => {
  const publicPath = (process.env.PUBLIC_PATH || '').replace(/\/$/, '');
  config.settings = {
    ...config.settings,
    nonContentRoutes: [
      ...config.settings.nonContentRoutes,
      `${publicPath}${EPICS_PATH_HEALTHZ}`,
      `${publicPath}${EPICS_PATH_CONTINUE}`,
      `${publicPath}${EPICS_PATH_CANCEL}`,
      `${publicPath}${EPICS_PATH_REDIRECT}`,
      `${publicPath}${EPICS_PATH_RAISE}`,
      new RegExp(`${publicPath}${EPICS_PATH_MESSAGE}/.*`),
      new RegExp(`${publicPath}${EPICS_PATH_TASK}/.*`),
      new RegExp(`${publicPath}${EPICS_PATH_START}/.*`),
      new RegExp(`${publicPath}${EPICS_PATH_ERROR}/.*`),
    ],
    appExtras: [
      ...config.settings.appExtras,
      {
        match: '',
        component: ContinuationStatus,
      },
    ],
    publicPath: publicPath,
    processApiPath: process.env.PROCESS_API_PATH || 'localhost:8000',
  };

  config.addonRoutes = [
    ...(config.addonRoutes || []),
    {
      path: EPICS_PATH_CONTINUE,
      component: ContinuationPollPage,
    },
    {
      path: `${EPICS_PATH_ERROR}/:uuid`,
      component: UnexpectedErrorPage,
    },
  ];

  config.addonReducers = {
    ...config.addonReducers,
  };

  if (__SERVER__) {
    const middleware = require('./middleware');
    config.settings.expressMiddleware = [
      ...config.settings.expressMiddleware,
      middleware.default(publicPath),
    ];
  }

  return config;
};

export default applyConfig;
