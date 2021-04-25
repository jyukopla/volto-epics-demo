/**
 * Redact variable values from data, but leave keys to signify existence of value.
 * @function redact
 * @params {Object} data Process data object.
 * @returns {Object} copy of data without variable values.
 */
import request from 'superagent';
import config from '@plone/volto/registry';
import { flattenToAppURL } from '@plone/volto/helpers/Url/Url';
import cookie from 'cookie';

export const redact = (data) => {
  const redacted = JSON.parse(JSON.stringify(data));
  if (redacted?.variables) {
    redacted.variables = Object.keys(data.variables).filter(
      (key) =>
        data.variables[key] !== null &&
        data.variables[key] !== undefined &&
        data.variables[key] !== '',
    );
  }
  if (redacted?.form) {
    redacted.form = Object.keys(data.form).filter(
      (key) =>
        data.form[key] !== null &&
        data.form[key] !== undefined &&
        data.form[key] !== '',
    );
  }
  return redacted;
};

/**
 * Get ExpressJS request cookie
 * @function getCookie
 * @param {req} req ExpressJS request.
 * @param {string} name Cookie name.
 * @returns {string} Cookie value.
 */
export const getCookie = (req, name) => {
  const cookies = cookie.parse(req.headers?.cookie ? req.headers.cookie : '');
  return cookies[name];
};

/**
 * Default cookie options
 * @function setCookie
 * @param {req} req ExpressJS request.
 * @param {res} res ExpressJS response.
 * @param {string} name Cookie name.
 * @param {string} value Cookie value.
 * @returns {string} Cookie value.
 */
export const setCookie = (req, res, name, value) => {
  res.cookie(name, value, cookieOptions(req));
};

/**
 * Clear ExpressJS response cookie
 * @function clearCookie
 * @param {req} req ExpressJS request.
 * @param {res} res Middleware response
 * @param {string} name Cookie name.
 */
export const clearCookie = (req, res, name) => {
  res.clearCookie(name, {
    ...cookieOptions(req),
    expires: new Date(1970, 1, 1, 0, 0, 1),
    maxAge: 0,
  });
};

/**
 * Default cookie options
 * @function cookieOptions
 * @param {req} req Middleware request.
 * @returns {object} Cookie options.
 */
export const cookieOptions = (req) => {
  const expires = new Date();
  expires.setHours(expires.getHours() + 2);
  return {
    path: '/',
    expires,
    httpOnly: true,
    secure: !req.headers.host.match(/^localhost:/),
  };
};

/**
 * Resolve Plone UUID
 * @function resolveUUID
 * @param {string} contentUid Plone content UUID
 * @param {string} authToken Plone auth token
 * @returns {string} matching Volto path
 */
export const resolveUUID = async (contentUid, authToken) => {
  let pathname;

  try {
    const resp = await (authToken
      ? request
          .get(`${config.settings.apiPath}/resolveuid/${contentUid}`)
          .set('Authorization', `Bearer ${authToken}`)
      : request.get(`${config.settings.apiPath}/resolveuid/${contentUid}`));

    if (resp.redirects.length > 0) {
      pathname = resp.redirects[0].replace(`${config.settings.apiPath}`, '');
    }
  } catch (e) {
    if (e?.response?.status === 301 || e?.response?.status === 302) {
      return flattenToAppURL(e?.response?.headers?.location);
    }
  }
  return pathname;
};
