import React, { useState } from 'react';
import { sendMessage, useContinuation } from 'volto-epics-addon/helpers';
import { toast } from 'react-toastify';
import ContinuationToast from 'volto-epics-addon/components/theme/Epics/ContinuationToast';
import {
  EPIC_TOAST_CONTINUATION,
  EPIC_TOAST_STATUS_MESSAGE,
  EPICS_TOAST_PROPS,
} from 'volto-epics-addon/constants';

const ContinuationStatus = ({ location, history }) => {
  const [stickyError, setStickyError] = useState(false);
  const [lastStatusMessage, setLastStatusMessage] = useState('');
  const continuation = useContinuation();
  const href = continuation?.location?.href;
  const pathname = continuation?.location?.pathname;
  const taskDefinitionKey = continuation?.taskDefinitionKey;
  const props = EPICS_TOAST_PROPS?.[continuation?.taskDefinitionKey];

  if (!href || !pathname || pathname === '/' || !taskDefinitionKey) {
    if (continuation?.errorMessage && !stickyError) {
      setToast(
        <ContinuationToast
          error
          autoClose={false}
          title={continuation.errorMessage}
          onClick={() => {
            toast.dismiss(EPIC_TOAST_CONTINUATION);
            setStickyError(false);
          }}
        />,
      );
      setStickyError(true);
    } else if (!stickyError) {
      toast.dismiss(EPIC_TOAST_CONTINUATION);
    }
  } else if (pathname === location.pathname && continuation?.errorMessage) {
    setToast(
      <ContinuationToast
        error
        title={continuation.errorMessage}
        onCancel={
          !!props?.showCancel
            ? async () => {
                await sendMessage('cancel');
              }
            : null
        }
      />,
    );
  } else if (
    pathname === location.pathname &&
    !!props?.title &&
    !!props?.showCancel
  ) {
    if (continuation?.statusMessage !== lastStatusMessage) {
      if (continuation?.statusMessage) {
        toast.success(
          <ContinuationToast success title={continuation.statusMessage} />,
          {
            toastId: EPIC_TOAST_STATUS_MESSAGE,
          },
        );
      }
      setLastStatusMessage(continuation?.statusMessage);
    }
    setToast(
      <ContinuationToast
        basic
        title={props.title}
        onCancel={async () => {
          await sendMessage('cancel');
        }}
      />,
    );
  } else if (pathname !== location.pathname && !!props?.title) {
    setToast(
      <ContinuationToast
        info
        title={props.title}
        type="continue"
        onClick={() => history.push(pathname)}
        onContinue={() => history.push(pathname)}
      />,
    );
  }
  return null;
};

const setToast = (Component) => {
  const basic = !!Component?.props?.basic;
  const error = !!Component?.props?.error;
  if (toast.isActive(EPIC_TOAST_CONTINUATION)) {
    toast.update(EPIC_TOAST_CONTINUATION, {
      type: basic
        ? toast.TYPE.DEFAULT
        : error
        ? toast.TYPE.ERROR
        : toast.TYPE.INFO,
      render: Component,
      closeOnClick: false,
      autoClose: false,
      closeButton: basic || error,
      onClick: Component?.props?.onClick,
    });
  } else {
    setTimeout(() => {
      (basic ? toast : error ? toast.error : toast.info)(Component, {
        closeOnClick: false,
        autoClose: false,
        toastId: EPIC_TOAST_CONTINUATION,
        closeButton: basic || error,
        onClick: Component?.props?.onClick,
      });
    }, 300);
  }
};

export default ContinuationStatus;
